/*

RERO ILS
Copyright (C) 2020 RERO
Copyright (C) 2017-2018 CERN.
Copyright (C) 2022-2023 Graz University of Technology.
Copyright (C) 2023      TU Wien.

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

const BundleTracker = require("webpack-bundle-tracker");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const ESLintPlugin = require("eslint-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const TerserPlugin = require("terser-webpack-plugin");
const config = require("./config");
const path = require("path");
const webpack = require("webpack");

// Load aliases from config and resolve their full path
let aliases = {};
if (config.aliases) {
  aliases = Object.fromEntries(
    Object.entries(config.aliases).map(([alias, alias_path]) => [
      alias,
      path.resolve(config.build.context, alias_path),
    ])
  );
}

var webpackConfig = {
  mode: process.env.NODE_ENV,
  entry: config.entry,
  context: config.build.context,
  stats: {
    warnings: true,
    errors: true,
    errorsCount: true,
    errorStack: true,
    errorDetails: true,
    children: true,
  },
  resolve: {
    extensions: ["*", ".js", ".jsx"],
    symlinks: false,
    alias: aliases,
    fallback: {
      zlib: require.resolve("browserify-zlib"),
      stream: require.resolve("stream-browserify"),
      https: require.resolve("https-browserify"),
      http: require.resolve("stream-http"),
      url: false,
      assert: false,
    },
  },
  output: {
    path: config.build.assetsPath,
    filename: "js/[name].[chunkhash].js",
    chunkFilename: "js/[id].[chunkhash].js",
    publicPath: config.build.assetsURL,
  },
  optimization: {
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          parse: {
            // We want terser to parse ecma 8 code. However, we don't want it
            // to apply any minification steps that turns valid ecma 5 code
            // into invalid ecma 5 code. This is why the 'compress' and 'output'
            // sections only apply transformations that are ecma 5 safe
            // https://github.com/facebook/create-react-app/pull/4234
            ecma: 8,
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
            inline: 2,
          },
          mangle: {
            safari10: true,
          },
          output: {
            ecma: 5,
            comments: false,
            // Turned on because emoji and regex is not minified properly using default
            // https://github.com/facebook/create-react-app/issues/2488
            ascii_only: true,
          },
        },
      }),
      new CssMinimizerPlugin(),
    ],
    splitChunks: {
      chunks: "all",
    },
    // Extract webpack runtime and module manifest to its own file in order to
    // prevent vendor hash from being updated whenever app bundle is updated.
    runtimeChunk: {
      name: "manifest",
    },
  },
  module: {
    rules: [
      {
        test: require.resolve("jquery"),
        use: [
          {
            loader: "expose-loader",
            options: {
              exposes: ["$", "jQuery"],
            },
          },
        ],
      },
      {
        test: /\.(js|jsx)$/,
        exclude: [/node_modules/, /@babel(?:\/|\\{1,2})runtime/],
        use: [
          {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env", "@babel/preset-react"],
              plugins: [
                "@babel/plugin-proposal-class-properties",
                "@babel/plugin-transform-runtime",
              ],
            },
          },
        ],
      },
      {
        test: /\.(scss|css)$/,
        use: [MiniCssExtractPlugin.loader, "css-loader", "sass-loader"],
      },
      {
        test: /\.(less)$/,
        use: [MiniCssExtractPlugin.loader, "css-loader", "less-loader"],
      },
      // Inline images smaller than 10k
      {
        test: /\.(png|jpe?g|gif|svg)(\?.*)?$/,
        type: "asset/inline",
        parser: {
          dataUrlCondition: {
            maxSize: 10 * 1024, // 10kb
          },
        },
      },
      // no mimetype for ".cur" in mimetype database, specify it with `generator`
      {
        test: /\.(cur)(\?.*)?$/,
        type: "asset/inline",
        generator: {
          dataUrl: {
            encoding: "base64",
            mimetype: "image/x-icon",
          },
        },
        parser: {
          dataUrlCondition: {
            maxSize: 10 * 1024, // 10kb
          },
        },
      },
      // Inline webfonts smaller than 10k
      {
        test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/,
        type: "asset/resource",
        generator: {
          filename: "fonts/[name].[contenthash:7].[ext]",
        },
        parser: {
          dataUrlCondition: {
            maxSize: 10 * 1024, // 10kb
          },
        },
      },
    ],
  },
  devtool:
    process.env.NODE_ENV === "production" ? "source-map" : "inline-source-map",
  plugins: [
    new ESLintPlugin({
      emitWarning: true,
      quiet: true,
      formatter: require("eslint-friendly-formatter"),
      eslintPath: require.resolve("eslint"),
    }),
    // Pragmas
    new webpack.DefinePlugin({
      "process.env": process.env.NODE_ENV,
    }),
    new MiniCssExtractPlugin({
      // Options similar to the same options in webpackOptions.output
      // both options are optional
      filename: "css/[name].[contenthash].css",
      chunkFilename: "css/[name].[contenthash].css",
    }),
    // Removes the dist folder before each run.
    new CleanWebpackPlugin({
      dry: false,
      verbose: false,
      dangerouslyAllowCleanPatternsOutsideProject: true,
      cleanStaleWebpackAssets: process.env.NODE_ENV === "production",   // keep stale assets in dev because of OS issues
    }),
    // Copying relevant CSS files as TinyMCE tries to import css files from the dist/js folder of static files
    new CopyWebpackPlugin({
      patterns: [
        {
          from: path.resolve(__dirname, '../node_modules/tinymce/skins/content/default/content.css'),
          to: path.resolve(config.build.assetsPath, 'js/skins/content/default'),
        },
        {
          from: path.resolve(__dirname, '../node_modules/tinymce/skins/ui/oxide/skin.min.css'),
          to: path.resolve(config.build.assetsPath, 'js/skins/ui/oxide'),
        },
        {
          from: path.resolve(__dirname, '../node_modules/tinymce/skins/ui/oxide/content.min.css'),
          to: path.resolve(config.build.assetsPath, 'js/skins/ui/oxide'),
        },
      ],
    }),
    // Automatically inject jquery
    new webpack.ProvidePlugin({
      jQuery: "jquery",
      $: "jquery",
      jquery: "jquery",
      "window.jQuery": "jquery",
    }),
    // Write manifest file which Python will read.
    new BundleTracker({
      path: config.build.assetsPath,
      filename: path.join(config.build.assetsPath, "manifest.json"),
      publicPath: config.build.assetsURL,
    }),
  ],
  performance: { hints: false },
  snapshot: {
    managedPaths: [],
  },
  watchOptions: {
    followSymlinks: true,
  },
};

if (process.env.npm_config_report) {
  var BundleAnalyzerPlugin =
    require("webpack-bundle-analyzer").BundleAnalyzerPlugin;
  webpackConfig.plugins.push(new BundleAnalyzerPlugin());
}

if (process.env.NODE_ENV === "development") {
  const LiveReloadPlugin = require("webpack-livereload-plugin");
  webpackConfig.plugins.push(new LiveReloadPlugin());
}

module.exports = webpackConfig;
