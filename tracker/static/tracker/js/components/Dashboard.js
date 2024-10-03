// tracker/static/tracker/js/components/Dashboard.js

import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useSpring, animated } from 'react-spring';
import { 
    Container, 
    Typography, 
    Paper, 
    Grid, 
    Select, 
    MenuItem, 
    FormControl, 
    InputLabel,
    ThemeProvider, 
    createTheme,
    CssBaseline,
    TextField
} from '@mui/material';
import axios from 'axios';

const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#90caf9',
        },
        secondary: {
            main: '#f48fb1',
        },
    },
});

const Dashboard = () => {
    const [sizeData, setSizeData] = useState({});
    const [configurations, setConfigurations] = useState([]);
    const [selectedConfigs, setSelectedConfigs] = useState([]);
    const [startDate, setStartDate] = useState('2024-01-01');
    const [endDate, setEndDate] = useState('2024-12-31');
    const [sections, setSections] = useState([]);

    const fadeIn = useSpring({
        opacity: 1,
        from: { opacity: 0 },
        config: { duration: 1000 }
    });

    useEffect(() => {
        fetchConfigurations();
    }, []);

    useEffect(() => {
        if (selectedConfigs.length > 0) {
            fetchSizeData();
        }
    }, [selectedConfigs, startDate, endDate]);

    const fetchConfigurations = async () => {
        try {
            const response = await axios.get('/api/configurations/');
            setConfigurations(response.data);
            setSelectedConfigs(response.data.map(config => config.id));
        } catch (error) {
            console.error('Error fetching configurations:', error);
        }
    };

    const fetchSizeData = async () => {
        try {
            const response = await axios.get('/api/size-measurements/size_evolution/', {
                params: {
                    start_date: startDate,
                    end_date: endDate,
                    config_ids: selectedConfigs.join(','),
                },
            });
            setSizeData(response.data);
            
            // Determine unique sections from the data
            const allSections = new Set();
            Object.values(response.data).forEach(configData => {
                configData.forEach(measurement => {
                    Object.keys(measurement).forEach(key => {
                        if (key !== 'date' && key !== 'total_size') {
                            allSections.add(key);
                        }
                    });
                });
            });
            setSections(Array.from(allSections));
        } catch (error) {
            console.error('Error fetching size data:', error);
        }
    };

    const handleConfigChange = (event) => {
        setSelectedConfigs(event.target.value);
    };

    const processChartData = () => {
        const allDates = new Set();
        const configData = {};

        Object.entries(sizeData).forEach(([configName, data]) => {
            data.forEach(item => {
                const date = new Date(item.date).toISOString().split('T')[0];
                allDates.add(date);
                if (!configData[date]) {
                    configData[date] = {};
                }
                sections.forEach(section => {
                    const sizeInMB = (item[section] || 0) / 1024 / 1024; // Convert to MB, use 0 if section is missing
                    configData[date][`${configName}_${section}`] = sizeInMB;
                });
            });
        });

        return Array.from(allDates).sort().map(date => ({
            date,
            ...configData[date]
        }));
    };

    const chartData = processChartData();

    const colors = [
        '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042',
        '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600', '#003f5c', '#2f4b7c', '#665191'
    ];

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Container maxWidth="lg">
                <animated.div style={fadeIn}>
                    <Typography variant="h2" component="h1" gutterBottom align="center" sx={{ mt: 4, mb: 4 }}>
                        Python Size Evolution
                    </Typography>
                    <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={4}>
                                <FormControl fullWidth>
                                    <InputLabel>Configurations</InputLabel>
                                    <Select
                                        multiple
                                        value={selectedConfigs}
                                        onChange={handleConfigChange}
                                        renderValue={(selected) => selected.map(id => configurations.find(c => c.id === id)?.name).join(', ')}
                                    >
                                        {configurations.map((config) => (
                                            <MenuItem key={config.id} value={config.id}>
                                                {config.name}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12} md={4}>
                                <TextField
                                    label="Start Date"
                                    type="date"
                                    value={startDate}
                                    onChange={(e) => setStartDate(e.target.value)}
                                    fullWidth
                                    InputLabelProps={{
                                        shrink: true,
                                    }}
                                />
                            </Grid>
                            <Grid item xs={12} md={4}>
                                <TextField
                                    label="End Date"
                                    type="date"
                                    value={endDate}
                                    onChange={(e) => setEndDate(e.target.value)}
                                    fullWidth
                                    InputLabelProps={{
                                        shrink: true,
                                    }}
                                />
                            </Grid>
                            <Grid item xs={12}>
                                {chartData.length > 0 ? (
                                    <ResponsiveContainer width="100%" height={600}>
                                        <AreaChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis 
                                                dataKey="date" 
                                                tick={{ fontSize: 12 }}
                                                tickFormatter={(tick) => new Date(tick).toLocaleDateString()}
                                            />
                                            <YAxis 
                                                label={{ value: 'Size (MB)', angle: -90, position: 'insideLeft' }} 
                                            />
                                            <Tooltip 
                                                formatter={(value) => value ? `${value.toFixed(2)} MB` : 'N/A'}
                                                labelFormatter={(label) => new Date(label).toLocaleDateString()}
                                            />
                                            <Legend />
                                            {Object.keys(sizeData).flatMap((configName) =>
                                                sections.map((section, index) => (
                                                    <Area
                                                        key={`${configName}_${section}`}
                                                        type="monotone"
                                                        dataKey={`${configName}_${section}`}
                                                        name={`${configName} - ${section}`}
                                                        stackId={configName}
                                                        fill={colors[index % colors.length]}
                                                        stroke={colors[index % colors.length]}
                                                    />
                                                ))
                                            )}
                                        </AreaChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <Typography variant="body1" align="center">
                                        No data available. Please select a configuration and date range.
                                    </Typography>
                                )}
                            </Grid>
                        </Grid>
                    </Paper>
                </animated.div>
            </Container>
        </ThemeProvider>
    );
};

export default Dashboard;