const path = require('path');

module.exports = {
    entry: {
        index: "./ts/index.ts"
    },

    output: {
        filename: "[name].js",
        path: path.resolve(__dirname, "../root/js")
    },

    mode: "none",

    resolve: {
        extensions: [".ts", ".tsx", ".js", ".json"]
    },

    module: {
        rules: [
            { test: /\.tsx?$/, loader: "ts-loader" },
        ]
    }
};
