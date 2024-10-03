const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');

module.exports = {
    entry: './tracker/static/tracker/js/index.js',
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, 'tracker', 'static', 'tracker', 'js'),
        publicPath: '/static/tracker/js/',
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: ['babel-loader']
            },
        ]
    },
    plugins: [
        new BundleTracker({
            path: __dirname,
            filename: 'webpack-stats.json'
        }),
    ],
};