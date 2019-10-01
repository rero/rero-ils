/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

const CleanWebpackPlugin = require('clean-webpack-plugin');
const config = require('./config');
const ManifestPlugin = require('webpack-manifest-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const safePostCssParser = require('postcss-safe-parser');
const TerserPlugin = require('terser-webpack-plugin');
const webpack = require('webpack');

var webpackConfig = {
  entry: config.entry,
  context: config.build.context,
  resolve: {
    extensions: ['*', '.js', '.jsx'],
    symlinks: false
  },
  output: {
    path: config.build.assetsPath,
    filename: 'js/[name].[chunkhash].js',
    chunkFilename: 'js/[id].[chunkhash].js',
    publicPath: config.build.assetsURL
  },
  optimization: {
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          parse: {
            // we want terser to parse ecma 8 code. However, we don't want it
            // to apply any minfication steps that turns valid ecma 5 code
            // into invalid ecma 5 code. This is why the 'compress' and 'output'
            // sections only apply transformations that are ecma 5 safe
            // https://github.com/facebook/create-react-app/pull/4234
            ecma: 8
          },
          compress: {
            ecma: 5,
            warnings: false,
            // Disabled because of an issue with Uglify breaking seemingly valid code:
            // https://github.com/facebook/create-react-app/issues/2376
            // Pending further investigation:
            // https://github.com/mishoo/UglifyJS2/issues/2011
            comparisons: false,
            // Disabled because of an issue with Terser breaking valid code:
            // https://github.com/facebook/create-react-app/issues/5250
            // Pending further investigation:
            // https://github.com/terser-js/terser/issues/120
            inline: 2
          },
          mangle: {
            safari10: true
          },
          output: {
            ecma: 5,
            comments: false,
            // Turned on because emoji and regex is not minified properly using default
            // https://github.com/facebook/create-react-app/issues/2488
            ascii_only: true
          }
        },
        // Use multi-process parallel running to improve the build speed
        // Default number of concurrent runs: os.cpus().length - 1
        parallel: true,
        cache: true
      }),
      new OptimizeCSSAssetsPlugin({
        cssProcessorOptions: {
          parser: safePostCssParser,
          map: false
        }
      })
    ],
    splitChunks: {
      cacheGroups: {
        commons: {
          test: /[\\/]node_modules[\\/]/,
          name: "vendor",
          chunks: "initial",
        },
      },
      chunks: 'all',
    },
    // Extract webpack runtime and module manifest to its own file in order to
    // prevent vendor hash from being updated whenever app bundle is updated.
    runtimeChunk: {
      name: 'manifest'
    }
  },
  module: {
    rules: [
      {
          test: require.resolve('jquery'),
          use: [{
              loader: 'expose-loader',
              options: 'jQuery'
          },{
              loader: 'expose-loader',
              options: '$'
          }]
      },
      {
        test: /\.(js|jsx)$/,
        exclude: [/node_modules/, /@babel(?:\/|\\{1,2})runtime/],
        use: [
          {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env", "@babel/preset-react"],
              plugins: ["@babel/plugin-proposal-class-properties", "@babel/plugin-transform-runtime"]
            }
          }
        ]
      },
      {
        test: /\.(js|jsx)$/,
        enforce: "pre",
        exclude: /node_modules/,
        use: [
          {
            options: {
              emitWarning: true,
              quiet: true,
              formatter: require('eslint-friendly-formatter'),
              eslintPath: require.resolve('eslint'),
            },
            loader: require.resolve('eslint-loader'),
          }
        ]
      },
      {
        test: /\.(scss|css)$/,
        use: [
          MiniCssExtractPlugin.loader,
            {
                loader: "css-loader",
                options: {
                    minimize: {
                        safe: true
                    }
                }
            },
            {
                loader: "sass-loader",
                options: {}
            }
        ]
      },
      // Inline images smaller than 10k
      {
        test: /\.(png|jpe?g|gif|svg)(\?.*)?$/,
        use: [
          {
            loader: require.resolve('url-loader'),
            options: {
              limit: 10000,
              name: 'img/[name].[hash:7].[ext]'
            }
          }
        ],
      },
      // Inline webfonts smaller than 10k
      {
        test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/,
        use: [
          {
            loader: require.resolve('file-loader'),
            options: {
              limit: 10000,
              name: 'fonts/[name].[hash:7].[ext]'
            }
          }
        ],
      }
    ]
  },
  // devtool: process.env.NODE_ENV === 'production' ? 'source-map' : 'cheap-source-map',
  plugins: [
    // Pragmas
    new webpack.DefinePlugin({
      'process.env': process.env.NODE_ENV
    }),
    new MiniCssExtractPlugin({
      // Options similar to the same options in webpackOptions.output
      // both options are optional
      filename: "css/[name].[contenthash].css",
      chunkFilename: "css/[name].[contenthash].css",
    }),
    // Removes the dist folder before each run.
    new CleanWebpackPlugin(config.build.assetsPath, {allowExternal: true}),
    // Automatically inject jquery
    new webpack.ProvidePlugin({
        jQuery: 'jquery/src/jquery',
        $: 'jquery/src/jquery',
        jquery: 'jquery/src/jquery',
        'window.jQuery': 'jquery/src/jquery'
    }),
    // Write manifest file which Python will read.
    new ManifestPlugin({
      fileName: 'manifest.json',
      stripSrc: true,
      publicPath: config.build.assetsURL
    })
  ],
  performance: { hints: false }
}

if (process.env.npm_config_report) {
  var BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin
  webpackConfig.plugins.push(new BundleAnalyzerPlugin())
}

module.exports = webpackConfig
