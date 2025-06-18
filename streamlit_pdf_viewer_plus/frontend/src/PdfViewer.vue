<template>
  <div id="pdfContainer" :style="pdfContainerStyle">
    <div v-if="args.rendering === 'unwrap'">
      <!-- PDF Toolbar -->
      <div class="pdf-toolbar" :style="toolbarStyle">
        <button 
          @click="goToPreviousPage" 
          :disabled="currentPage <= 1"
          class="nav-button"
          title="Previous Page"
        >
          ‹
        </button>
        
        <div class="page-info">
          <input 
            v-model="pageInputValue"
            @keyup.enter="goToPage"
            @blur="goToPage"
            @input="validatePageInput"
            type="number"
            :min="1"
            :max="totalPages"
            class="page-input"
          />
          <span class="page-separator">/ {{ totalPages }}</span>
        </div>
        
        <button 
          @click="goToNextPage" 
          :disabled="currentPage >= totalPages"
          class="nav-button"
          title="Next Page"
        >
          ›
        </button>
        
        <!-- Zoom Controls -->
        <div class="zoom-controls">
          <button 
            @click="zoomOut" 
            :disabled="currentZoom <= minZoom"
            class="zoom-button"
            title="Zoom Out"
          >
            -
          </button>
          
          <span class="zoom-display">{{ Math.round(currentZoom * 100) }}%</span>
          
          <button 
            @click="zoomIn" 
            :disabled="currentZoom >= maxZoom"
            class="zoom-button"
            title="Zoom In"
          >
            +
          </button>
          
          <button 
            @click="resetZoom"
            class="zoom-reset-button"
            title="Reset Zoom"
          >
            Reset
          </button>
        </div>
      </div>
      
      <div id="pdfViewer" :style="pdfViewerStyle"></div>
    </div>
    <div v-else-if="args.rendering === 'legacy_embed'">
      <embed :src="`data:application/pdf;base64,${args.binary}`" :width="`${args.width}`" :height="`${args.height}`"
             type="application/pdf"/>
    </div>
    <div v-else-if="args.rendering === 'legacy_iframe'">
      <embed :src="`data:application/pdf;base64,${args.binary}`" :width="`${args.width}`" :height="`${args.height}`"
             type="application/pdf"/>
    </div>
    <div v-else>
      Error rendering option.
    </div>
  </div>
</template>

<script>
import { onMounted, computed, ref, onUnmounted } from "vue";
import "pdfjs-dist/web/pdf_viewer.css";
import "pdfjs-dist/build/pdf.worker.mjs";
import { getDocument, GlobalWorkerOptions } from "pdfjs-dist/build/pdf";
import { Streamlit } from "streamlit-component-lib";
import { TextLayer } from "pdfjs-dist";
import debounce from 'lodash/debounce';

const CMAP_URL = "pdfjs-dist/cmaps/";
const CMAP_PACKED = true;
const ENABLE_XFA = true;
const acceptedBorderStyleAttributes = ['solid', 'dashed', 'dotted', 'double', 'groove', 'ridge', 'inset', 'outset', 'none', undefined, null];

export default {
  props: ["args"],

  setup(props) {
    const totalHeight = ref(0);
    const maxWidth = ref(0);
    const pageScales = ref([]);
    const pageHeights = ref([]);
    const loadedPages = ref([]);
    const currentFrameHeight = ref(props.args.height || 0);
    
    // Newly added reactive variables
    const currentPage = ref(1);
    const totalPages = ref(0);
    const pageInputValue = ref(1);
    
    // Zoom-related reactive variables
    const currentZoom = ref(1.0);
    const minZoom = ref(0.5);
    const maxZoom = ref(3.0);
    const zoomStep = ref(0.25);
    const baseScale = ref(1.0);

    // Initialize container width
    const initializeMaxWidth = () => {
      const result = parseWidthValue(props.args.width);
      if (result.type === "percent") {
        maxWidth.value = Math.floor(result.value * window.innerWidth);
      } else {
        maxWidth.value = result.value;
      }
      // Ensure a reasonable minimum width and don't exceed window width
      maxWidth.value = Math.max(maxWidth.value, 300); // Minimum width 300px
      maxWidth.value = Math.min(maxWidth.value, window.innerWidth);
    };

    const isRenderingAllPages = props.args.pages_to_render.length === 0;

    const renderText = props.args.render_text === true;

    const parseWidthValue = (widthValue, fallbackValue = window.innerWidth) => {
      // If no width is specified, default to 100%
      if (!widthValue) {
        return { type: "percent", value: 1.0 };
      }
      
      if (typeof widthValue === "string" && widthValue.endsWith("%")) {
        const num = parseFloat(widthValue);
        if (!isNaN(num)) {
          return { type: "percent", value: num / 100 };
        }
      }
      const numeric = Number(widthValue);
      if (!isNaN(numeric) && numeric > 0) {
        return { type: "pixel", value: numeric };
      }
      return { type: "percent", value: 1.0 }; // Default 100%
    };

    const pdfContainerStyle = computed(() => {
      const result = parseWidthValue(props.args.width);
      const widthCSS = result.type === "percent" ? `${result.value * 100}%` : `${result.value}px`;
      return {
        width: widthCSS,
        height: props.args.height ? `${props.args.height}px` : 'auto',
        overflow: 'auto',
        position: 'relative',
      };
    });

    const pdfViewerStyle = { position: 'relative' };

    // Toolbar style
    const toolbarStyle = computed(() => ({
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '10px',
      padding: '8px 16px',
      backgroundColor: '#f5f5f5',
      borderBottom: '1px solid #ddd',
      position: 'sticky',
      top: '0',
      zIndex: 1000, // Increased z-index to ensure it stays on top
      fontSize: '14px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)', // Add shadow for better visibility
      width: '100%',
      boxSizing: 'border-box'
    }));

    const calculatePdfsHeight = (page) => {
      let height = 0;
      if (isRenderingAllPages) {
        for (let i = 0; i < page - 1; i++) {
          height += pageHeights.value[i] * pageScales.value[i] + props.args.pages_vertical_spacing;
        }
      } else {
        for (let i = 0; i < pageHeights.value.length; i++) {
          if (props.args.pages_to_render.includes(i + 1) && i < page - 1) {
            height += pageHeights.value[i] * pageScales.value[i] + props.args.pages_vertical_spacing;
          }
        }
      }
      return height;
    };

    const clearExistingCanvases = (pdfViewer) => {
      if (!pdfViewer) return;
      pdfViewer.innerHTML = '';
    };

    const createCanvasForPage = (page, scale, rotation, pageNumber, resolutionRatioBoost = 1) => {
      const viewport = page.getViewport({ scale, rotation });
      const ratio = (window.devicePixelRatio || 1) * resolutionRatioBoost;

      const canvas = document.createElement("canvas");
      canvas.id = `canvas_page_${pageNumber}`;
      canvas.height = viewport.height * ratio;
      canvas.width = viewport.width * ratio;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      canvas.style.display = "block";
      canvas.getContext("2d").scale(ratio, ratio);

      return canvas;
    };

    const renderAnnotation = (annotation, annotationIndex, pageDiv, scale) => {
      const annotationDiv = document.createElement('div');
      annotation.id = `${annotation.id || annotationIndex}`
      annotationDiv.id = `annotation-${annotation.id}`;
      annotationDiv.setAttribute("data-index", annotation.id);
      annotationDiv.style.position = 'absolute';
      annotationDiv.style.left = `${annotation.x * scale}px`;
      annotationDiv.style.top = `${annotation.y * scale}px`;
      annotationDiv.style.width = `${annotation.width * scale}px`;
      annotationDiv.style.height = `${annotation.height * scale}px`;
      let border = annotation.border
      if (!annotation.border || !acceptedBorderStyleAttributes.includes(annotation.border)) {
        border = "solid"
      }
      annotationDiv.style.outline = `${props.args.annotation_outline_size * scale}px ${border} ${annotation.color}`;
      annotationDiv.style.cursor = renderText ? 'text' : 'pointer';
      annotationDiv.style.pointerEvents = renderText ? 'none' : 'auto';
      annotationDiv.style.zIndex = 10;

      if (!renderText) {
        annotationDiv.addEventListener('click', () => {
          Streamlit.setComponentValue({
            clicked_annotation: { index: annotation.id, ...annotation },
          });
        });
      }

      pageDiv.appendChild(annotationDiv);
    };

    const renderPage = async (page, canvas, viewport, annotations, annotationCount) => {
      const renderContext = {
        canvasContext: canvas.getContext("2d"),
        viewport: viewport
      };

      await page.render(renderContext).promise;

      const pageDiv = document.createElement('div');
      pageDiv.className = 'page';
      pageDiv.style.position = 'relative';
      pageDiv.style.width = `${viewport.width}px`;
      pageDiv.style.height = `${viewport.height}px`;
      pageDiv.style.marginBottom = `${props.args.pages_vertical_spacing}px`;

      const canvasWrapper = document.createElement('div');
      canvasWrapper.className = 'canvasWrapper';
      canvasWrapper.style.position = 'absolute';
      canvasWrapper.style.top = '0';
      canvasWrapper.style.left = '0';
      canvasWrapper.appendChild(canvas);

      pageDiv.appendChild(canvasWrapper);

      if (renderText) {
        const textContent = await page.getTextContent();
        const textLayerDiv = document.createElement("div");
        textLayerDiv.className = "textLayer";
        textLayerDiv.style.zIndex = "11";
        textLayerDiv.style.position = 'absolute';
        textLayerDiv.style.top = '0';
        textLayerDiv.style.left = '0';
        textLayerDiv.style.height = `${viewport.height}px`;
        textLayerDiv.style.width = `${viewport.width}px`;

        const textLayer = new TextLayer({
          textContentSource: textContent,
          container: textLayerDiv,
          viewport: viewport,
          textDivs: []
        });
        await textLayer.render();

        pageDiv.appendChild(textLayerDiv);
      }

      if (annotations && annotations.length > 0) {
        annotations.forEach((annotation, index) => {
          const annotationUniqueIndex = annotationCount + index;
          renderAnnotation(annotation, annotationUniqueIndex, pageDiv, viewport.scale);
        });
      }

      const pdfViewer = document.getElementById("pdfViewer");
      pdfViewer.appendChild(pageDiv);
    };

    const getPagesToRender = (numPages) => {
      if (props.args.pages_to_render.length === 0) {
        return Array.from({ length: numPages }, (_, i) => i + 1);
      }
      return props.args.pages_to_render;
    };

    const renderPdfPages = async (pdf, pdfViewer, pagesToRender) => {
      totalHeight.value = 0;
      pageScales.value = [];
      pageHeights.value = [];
      loadedPages.value = [];
      
      // Set total pages
      totalPages.value = pdf.numPages;
      
      // Ensure current page and page input are within valid range
      if (currentPage.value < 1) {
        currentPage.value = 1;
      } else if (currentPage.value > totalPages.value) {
        currentPage.value = totalPages.value;
      }
      pageInputValue.value = currentPage.value;

      const resolutionBoost = props.args.resolution_boost || 1;

      let annotationCount = 0;

      for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
        const page = await pdf.getPage(pageNumber);
        const rotation = page.rotate;
        const unscaledViewport = page.getViewport({ scale: 1.0, rotation });

        // Calculate scale ratio: make PDF width fill container width
        const scale = (maxWidth.value / unscaledViewport.width) * currentZoom.value;
        
        // Store base scale ratio (on first calculation)
        if (pageNumber === 1 && baseScale.value === 1.0) {
          baseScale.value = maxWidth.value / unscaledViewport.width;
        }

        pageScales.value.push(scale);
        pageHeights.value.push(unscaledViewport.height);

        if (pagesToRender.includes(pageNumber)) {
          const canvas = createCanvasForPage(page, scale, rotation, pageNumber, resolutionBoost);
          pdfViewer.style.setProperty('--scale-factor', scale);

          const viewport = page.getViewport({
            scale: scale,
            rotation: rotation,
            intent: "print",
          });

          const annotationsForPage = props.args.annotations.filter(
            anno => Number(anno.page) === pageNumber
          );

          totalHeight.value += canvas.height / ((window.devicePixelRatio || 1) * resolutionBoost);
          await renderPage(page, canvas, viewport, annotationsForPage, annotationCount);
          annotationCount += annotationsForPage.length

          if (canvas.id) {
            loadedPages.value.push(canvas.id);
          }
        }
      }
      // Subtract the margin for the last page as it's not needed
      if (pagesToRender.length > 0) {
        totalHeight.value -= props.args.pages_vertical_spacing;
      }
    };

    const alertError = (error) => {
      console.error(error);
      window.alert(error.message);
    };

    const loadPdfs = async (url) => {
      GlobalWorkerOptions.workerSrc = 'pdfjs-dist/build/pdf.worker.mjs';
      try {
        const loadingTask = getDocument({
          url: url,
          cMapUrl: CMAP_URL,
          cMapPacked: CMAP_PACKED,
          enableXfa: ENABLE_XFA,
        });
        const pdf = await loadingTask.promise;

        const pdfViewer = document.getElementById("pdfViewer");
        clearExistingCanvases(pdfViewer);

        const pagesToRender = getPagesToRender(pdf.numPages);
        await renderPdfPages(pdf, pdfViewer, pagesToRender);
        scrollToItem();
      } catch (error) {
        alertError(error);
      }
    };

    // Page navigation methods
    const updateCurrentPage = () => {
      // Determine current page number by checking currently visible pages
      const pdfContainer = document.getElementById("pdfContainer");
      if (!pdfContainer) return;

      const containerRect = pdfContainer.getBoundingClientRect();
      const containerTop = containerRect.top;
      const containerBottom = containerRect.bottom;

      let visiblePage = currentPage.value; // Start with current page instead of 1
      let maxVisibleArea = 0;

      for (let i = 1; i <= totalPages.value; i++) {
        const pageElement = document.getElementById(`canvas_page_${i}`);
        if (pageElement) {
          const pageRect = pageElement.getBoundingClientRect();
          
          // Calculate visible area of the page
          const visibleTop = Math.max(pageRect.top, containerTop);
          const visibleBottom = Math.min(pageRect.bottom, containerBottom);
          const visibleHeight = Math.max(0, visibleBottom - visibleTop);
          const visibleArea = visibleHeight * pageRect.width;
          
          if (visibleArea > maxVisibleArea) {
            maxVisibleArea = visibleArea;
            visiblePage = i;
          }
        }
      }
      
      // Only update if we found a page with visible area or if current page is invalid
      if (maxVisibleArea > 0 || currentPage.value < 1 || currentPage.value > totalPages.value) {
        if (currentPage.value !== visiblePage) {
          currentPage.value = visiblePage;
          pageInputValue.value = visiblePage;
        }
      }
    };

    // Validate and fix page input value
    const validatePageInput = () => {
      if (pageInputValue.value < 1) {
        pageInputValue.value = 1;
      } else if (pageInputValue.value > totalPages.value) {
        pageInputValue.value = totalPages.value;
      }
    };

    const goToPage = () => {
      validatePageInput(); // Ensure input is valid before processing
      const targetPage = parseInt(pageInputValue.value);
      if (targetPage >= 1 && targetPage <= totalPages.value) {
        const pageElement = document.getElementById(`canvas_page_${targetPage}`);
        if (pageElement) {
          pageElement.scrollIntoView({ behavior: "smooth" });
          currentPage.value = targetPage;
        } else {
          // If page element not found, restore to current page number
          pageInputValue.value = currentPage.value;
        }
      } else {
        // If input is invalid, restore to current page number
        pageInputValue.value = currentPage.value;
      }
    };

    const goToPreviousPage = () => {
      if (currentPage.value > 1 && totalPages.value > 0) {
        pageInputValue.value = currentPage.value - 1;
        goToPage();
      }
    };

    const goToNextPage = () => {
      if (currentPage.value < totalPages.value && totalPages.value > 0) {
        pageInputValue.value = currentPage.value + 1;
        goToPage();
      }
    };

    // Zoom related methods
    const zoomIn = async () => {
      const newZoom = Math.min(currentZoom.value + zoomStep.value, maxZoom.value);
      if (newZoom !== currentZoom.value) {
        currentZoom.value = newZoom;
        await refreshPdfPages();
      }
    };

    const zoomOut = async () => {
      const newZoom = Math.max(currentZoom.value - zoomStep.value, minZoom.value);
      if (newZoom !== currentZoom.value) {
        currentZoom.value = newZoom;
        await refreshPdfPages();
      }
    };

    const resetZoom = async () => {
      if (currentZoom.value !== 1.0) {
        currentZoom.value = 1.0;
        await refreshPdfPages();
      }
    };

    // Refresh PDF pages (apply new zoom)
    const refreshPdfPages = async () => {
      try {
        const binaryDataUrl = `data:application/pdf;base64,${props.args.binary}`;
        const loadingTask = getDocument({
          url: binaryDataUrl,
          cMapUrl: CMAP_URL,
          cMapPacked: CMAP_PACKED,
          enableXfa: ENABLE_XFA,
        });
        const pdf = await loadingTask.promise;
        const pdfViewer = document.getElementById("pdfViewer");
        clearExistingCanvases(pdfViewer);
        const pagesToRender = getPagesToRender(pdf.numPages);
        await renderPdfPages(pdf, pdfViewer, pagesToRender);
        setFrameHeight();
      } catch (error) {
        alertError(error);
      }
    };

    const scrollToItem = () => {
      if (props.args.scroll_to_page) {
        const page = document.getElementById(`canvas_page_${props.args.scroll_to_page}`);
        if (page) {
          page.scrollIntoView({ behavior: "smooth" });
          // Update current page after scrolling
          setTimeout(() => {
            currentPage.value = props.args.scroll_to_page;
            pageInputValue.value = props.args.scroll_to_page;
          }, 500);
        }
      } else if (props.args.scroll_to_annotation) {
        const annotation = document.querySelector(`[id^="annotation-"][data-index="${props.args.scroll_to_annotation}"]`);
        if (annotation) {
          annotation.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }
    };

    const setFrameHeight = () => {
      const newHeight = props.args.height || totalHeight.value;
      if (newHeight !== currentFrameHeight.value) {
        Streamlit.setFrameHeight(newHeight);
        currentFrameHeight.value = newHeight;
      }
    };

    const setFrameWidth = () => {
      const result = parseWidthValue(props.args.width);
      let newMaxWidth;
      if (result.type === "percent") {
        newMaxWidth = Math.floor(result.value * window.innerWidth);
      } else {
        newMaxWidth = result.value;
      }

      // Ensure a reasonable minimum width and don't exceed window width
      newMaxWidth = Math.max(newMaxWidth, 300); // Minimum width 300px
      newMaxWidth = Math.min(newMaxWidth, window.innerWidth);

      if (newMaxWidth !== maxWidth.value) {
        maxWidth.value = newMaxWidth;
      }
    };

    const handleResize = async () => {
      try {
        console.log('handleResize');
        if (props.args.rendering === "unwrap") {
          setFrameWidth(); // Set width first
          const binaryDataUrl = `data:application/pdf;base64,${props.args.binary}`;
          await loadPdfs(binaryDataUrl);
          setFrameHeight();
        }
      } catch (error) {
        console.error(error);
      }
    };

    // Debounced resize handler to prevent multiple rapid executions
    const debouncedHandleResize = debounce(handleResize, 200);
    
    // Debounced scroll handler to update current page
    const debouncedUpdateCurrentPage = debounce(updateCurrentPage, 100);
    
    // Fix toolbar visibility issues in Streamlit containers
    const ensureToolbarVisibility = () => {
      const toolbar = document.querySelector('.pdf-toolbar');
      if (toolbar) {
        // Force re-render of sticky positioning
        toolbar.style.position = 'sticky';
        toolbar.style.top = '0';
        toolbar.style.zIndex = '1000';
      }
    };
    
    const debouncedEnsureToolbarVisibility = debounce(ensureToolbarVisibility, 100);

    onMounted(() => {
      initializeMaxWidth(); // Initialize container width first
      debouncedHandleResize();
      window.addEventListener("resize", debouncedHandleResize);
      
      // Add scroll listener to PDF container
      const pdfContainer = document.getElementById("pdfContainer");
      if (pdfContainer) {
        pdfContainer.addEventListener("scroll", debouncedUpdateCurrentPage);
        pdfContainer.addEventListener("scroll", debouncedEnsureToolbarVisibility);
      }
      
      // Ensure toolbar is visible after initial load
      setTimeout(ensureToolbarVisibility, 100);
    });

    onUnmounted(() => {
      window.removeEventListener("resize", debouncedHandleResize);
      
      // Remove scroll listeners
      const pdfContainer = document.getElementById("pdfContainer");
      if (pdfContainer) {
        pdfContainer.removeEventListener("scroll", debouncedUpdateCurrentPage);
        pdfContainer.removeEventListener("scroll", debouncedEnsureToolbarVisibility);
      }
    });

    return {
      pdfContainerStyle,
      pdfViewerStyle,
      currentPage,
      pageInputValue,
      totalPages,
      toolbarStyle,
      goToPreviousPage,
      goToNextPage,
      goToPage,
      validatePageInput,
      // Zoom related
      currentZoom,
      minZoom,
      maxZoom,
      zoomIn,
      zoomOut,
      resetZoom,
    };
  },
};
</script>

<style>
/* Basic styles for PDF container and pages */
#pdfContainer {
  box-sizing: border-box;
  /* Ensure proper stacking context for sticky positioning */
  position: relative;
  overflow: auto;
  /* Fix for Streamlit container issues */
  height: 100%;
}

/* Specific fixes for Streamlit containers */
.element-container #pdfContainer {
  position: relative !important;
}

.stContainer #pdfContainer {
  overflow: auto !important;
}

#pdfViewer {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.page {
  max-width: 100%;
  box-sizing: border-box;
}

.page canvas {
  max-width: 100%;
  height: auto;
  display: block;
}

.canvasWrapper {
  width: 100%;
  display: flex;
  justify-content: center;
}

.pdf-toolbar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #ddd;
  position: sticky;
  top: 0;
  z-index: 1000; /* Increased z-index */
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  /* Force the toolbar to stay on top in all contexts */
  position: -webkit-sticky; /* Safari support */
  
  /* Additional fixes for Streamlit containers */
  width: 100%;
  box-sizing: border-box;
  /* Ensure it works in various container contexts */
  transform: translateZ(0); /* Force hardware acceleration */
  will-change: transform; /* Optimize for changes */
}

.nav-button {
  cursor: pointer;
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background-color: #007bff;
  color: white;
  font-size: 18px;
  font-weight: bold;
  min-width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.nav-button:hover:not(:disabled) {
  background-color: #0056b3;
}

.nav-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.page-info {
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-input {
  width: 50px;
  height: 32px;
  text-align: center;
  font-size: 14px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 4px;
  outline: none;
}

.page-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.page-separator {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

/* Zoom control styles */
.zoom-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 20px;
  padding-left: 20px;
  border-left: 1px solid #ddd;
}

.zoom-button {
  cursor: pointer;
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  background-color: #28a745;
  color: white;
  font-size: 16px;
  font-weight: bold;
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.zoom-button:hover:not(:disabled) {
  background-color: #218838;
}

.zoom-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.zoom-display {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  min-width: 50px;
  text-align: center;
  background-color: #f8f9fa;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

.zoom-reset-button {
  cursor: pointer;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background-color: #6c757d;
  color: white;
  font-size: 12px;
  font-weight: 500;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.zoom-reset-button:hover {
  background-color: #5a6268;
}
</style>
