#!/bin/bash

# Exit on error
set -e

# Ensure we're in the project directory
if [ ! -d "weightlifter" ]; then
    echo "Please run this script from the directory containing the 'weightlifter' folder."
    exit 1
fi

cd weightlifter

# Create necessary directories
mkdir -p tracker/static/tracker/js
mkdir -p tracker/templates/tracker

# Set up npm and install dependencies
npm init -y
npm install webpack webpack-cli babel-loader @babel/core @babel/preset-env @babel/preset-react react react-dom axios recharts @mui/material @mui/icons-material @emotion/react @emotion/styled webpack-bundle-tracker

# Create webpack configuration file
cat << EOF > webpack.config.js
const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');

module.exports = {
    entry: './tracker/static/tracker/js/index.js',
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, './tracker/static/tracker/js/'),
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
        new BundleTracker({filename: './webpack-stats.json'}),
    ],
};
EOF

# Create .babelrc file
cat << EOF > .babelrc
{
  "presets": ["@babel/preset-env", "@babel/preset-react"]
}
EOF

# Create main React component
cat << EOF > tracker/static/tracker/js/index.js
import React from 'react';
import ReactDOM from 'react-dom';
import Dashboard from './components/Dashboard';

ReactDOM.render(<Dashboard />, document.getElementById('react-app'));
EOF

# Create Dashboard component
mkdir -p tracker/static/tracker/js/components
cat << EOF > tracker/static/tracker/js/components/Dashboard.js
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const Dashboard = () => {
    const [sizeData, setSizeData] = useState([]);
    const [configurations, setConfigurations] = useState([]);
    const [selectedConfigs, setSelectedConfigs] = useState([]);

    useEffect(() => {
        fetchConfigurations();
    }, []);

    useEffect(() => {
        if (selectedConfigs.length > 0) {
            fetchSizeData();
        }
    }, [selectedConfigs]);

    const fetchConfigurations = async () => {
        const response = await axios.get('/api/configurations/');
        setConfigurations(response.data);
    };

    const fetchSizeData = async () => {
        const response = await axios.get('/api/size-measurements/size_evolution/', {
            params: {
                start_date: '2023-01-01',
                end_date: '2023-12-31',
                config_ids: selectedConfigs.join(','),
            },
        });
        setSizeData(response.data);
    };

    const handleConfigChange = (event) => {
        setSelectedConfigs(Array.from(event.target.selectedOptions, option => option.value));
    };

    return (
        <div>
            <h1>Python Size Evolution</h1>
            <select multiple value={selectedConfigs} onChange={handleConfigChange}>
                {configurations.map((config) => (
                    <option key={config.id} value={config.id}>
                        {config.name}
                    </option>
                ))}
            </select>
            <ResponsiveContainer width="100%" height={400}>
                <LineChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {Object.entries(sizeData).map(([configName, data]) => (
                        <Line
                            key={configName}
                            type="monotone"
                            dataKey="total_size"
                            data={data}
                            name={configName}
                            stroke={\`#\${Math.floor(Math.random()*16777215).toString(16)}\`}
                        />
                    ))}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export default Dashboard;
EOF

# Create Django template for the dashboard
cat << EOF > tracker/templates/tracker/dashboard.html
{% load static %}
{% load render_bundle from webpack_loader %}

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weightlifter Dashboard</title>
</head>
<body>
    <div id="react-app"></div>
    {% render_bundle 'main' %}
</body>
</html>
EOF

# Add build script to package.json
sed -i 's/"scripts": {/"scripts": {\n    "build": "webpack --mode production",/' package.json

echo "Frontend setup complete. Please update your Django settings and views to integrate the frontend."
echo "Run 'npm run build' to build the frontend, then start your Django server."
