const {VueLoaderPlugin} = require('vue-loader');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  publicPath: './',
  configureWebpack: {
    target: 'web',
    module: {
      rules: [
        {
          test: /\.(js|mjs)$/,
          include: /node_modules\/pdfjs-dist/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: [['@babel/preset-env', {targets: {esmodules: true}}]],
            }
          }
        }
      ]
    },
    plugins: [
      new VueLoaderPlugin(),
      new CopyWebpackPlugin({patterns:[
        {
          from: 'node_modules/pdfjs-dist/cmaps/',
          to: 'pdfjs-dist/cmaps/'
        }
      ]})
      // new BundleAnalyzerPlugin()
    ],
  }
}