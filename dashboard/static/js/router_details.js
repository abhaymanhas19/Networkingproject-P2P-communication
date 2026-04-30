/**
 * Author: Ely Millan <eleuteriomillanjr@@gmail.com>
 * Date: 2023-06-14
 * Description: This file contains the code for the router details page.
 *
 * Enhanced by: Claude (Anthropic)
 * Date: 2026-APR-30
 * Changes:
 *   - renderBandwidthChart: switched from line to bar chart for clearer per-sample
 *     visibility; added auto-detected spike highlighting (3× median threshold) with
 *     orange triangle markers; injected a summary metrics row (peak DL, avg DL,
 *     peak UL) above the chart dynamically — no HTML changes required.
 *   - renderUptimeChart: y-axis now starts just below the data minimum instead of
 *     always at 0, making small dips visible; title dynamically shows the average
 *     uptime %; removed point markers for a cleaner line; removed downtime event
 *     markers per client request.
 */


/**
 * Converts bits per second (bps) to megabits per second (Mbps).
 *
 * @param {number} bps - The bits per second to convert.
 * @return {number} The megabits per second.
 */
function convertBpsToMbps(bps) {
    return bps / 1_000_000;
  }


/**
 * Renders a bar chart displaying bandwidth data.
 *
 * Original: rendered as a line chart with teal/purple colours.
 * Enhanced: switched to bar chart; spikes auto-detected at 3× median and
 * highlighted with a darker green fill + orange triangle scatter marker;
 * summary metric cards (peak DL, avg DL, peak UL) injected above the chart.
 *
 * @param {string} data - The bandwidth data in JSON format.
 * @param {CanvasRenderingContext2D} ctx - The rendering context for the chart.
 * @param {string} chartName - The global window key to store the chart instance.
 * @return {void}
 */
function renderBandwidthChart(data, ctx, chartName) {

    data = JSON.parse(data);
    const downlinkThroughputMbps = data.data_series.downlinkThroughputBps.map(convertBpsToMbps);
    const uplinkThroughputMbps = data.data_series.uplinkThroughputBps.map(convertBpsToMbps);

    const dlReversed = downlinkThroughputMbps.reverse(); // Reverse the data series to match the labels
    const ulReversed = uplinkThroughputMbps.reverse();   // Reverse the data series to match the labels
    const labelsReversed = data.labels.reverse();        // Reverse the labels to maintain chronological order

    // Auto-detect spikes: any point more than 3× the median is considered a spike.
    // Falls back to 0.1 Mbps minimum so near-zero baselines don't false-positive.
    const sorted = [...dlReversed].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)] || 0;
    const spikeThreshold = Math.max(median * 3, 0.1);

    // Compute summary values for the metric cards
    const peakDl = Math.max(...dlReversed).toFixed(3);
    const avgDl  = (dlReversed.reduce((a, b) => a + b, 0) / dlReversed.length).toFixed(3);
    const peakUl = Math.max(...ulReversed).toFixed(3);

    // Inject summary metric cards above the chart (idempotent — skipped if already present)
    const canvas = ctx.canvas;
    const wrapper = canvas.closest('.chart-container') || canvas.parentElement;
    if (!wrapper.parentElement.querySelector('.p2p-bw-metrics')) {
        const metricsHtml = `
        <div class="p2p-bw-metrics" style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px;">
            <div style="background:#f9fafb;border-radius:8px;padding:10px 14px;border:1px solid #e5e7eb;">
                <div style="font-size:11px;color:#6b7280;margin-bottom:4px;">Peak download</div>
                <div style="font-size:18px;font-weight:500;color:#0F6E56;">${peakDl} <span style="font-size:12px;font-weight:400">Mbps</span></div>
            </div>
            <div style="background:#f9fafb;border-radius:8px;padding:10px 14px;border:1px solid #e5e7eb;">
                <div style="font-size:11px;color:#6b7280;margin-bottom:4px;">Avg download</div>
                <div style="font-size:18px;font-weight:500;color:#374151;">${avgDl} <span style="font-size:12px;font-weight:400">Mbps</span></div>
            </div>
            <div style="background:#f9fafb;border-radius:8px;padding:10px 14px;border:1px solid #e5e7eb;">
                <div style="font-size:11px;color:#6b7280;margin-bottom:4px;">Peak upload</div>
                <div style="font-size:18px;font-weight:500;color:#7F77DD;">${peakUl} <span style="font-size:12px;font-weight:400">Mbps</span></div>
            </div>
        </div>`;
        wrapper.insertAdjacentHTML('beforebegin', metricsHtml);
    }

    const myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labelsReversed,
            datasets: [
                {
                    label: 'Download',
                    data: dlReversed,
                    // Spike bars get a darker green; normal bars use the standard teal
                    backgroundColor: dlReversed.map(v => v > spikeThreshold ? 'rgba(15,110,86,0.85)' : 'rgba(29,158,117,0.55)'),
                    borderColor: dlReversed.map(v => v > spikeThreshold ? '#0F6E56' : '#1D9E75'),
                    borderWidth: dlReversed.map(v => v > spikeThreshold ? 1.5 : 0.5),
                    borderRadius: 2,
                    order: 1
                },
                {
                    label: 'Upload',
                    data: ulReversed,
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 0.5,
                    borderRadius: 2,
                    order: 2
                },
                {
                    // Scatter overlay marks spike positions with an orange triangle
                    label: 'Spike',
                    type: 'scatter',
                    data: labelsReversed
                        .map((label, i) => dlReversed[i] > spikeThreshold ? { x: label, y: dlReversed[i] * 1.08 } : null)
                        .filter(Boolean),
                    backgroundColor: '#D85A30',
                    pointStyle: 'triangle',
                    radius: 7,
                    order: 0
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '24 hours Bandwidth (DL/UL)'
                },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            if (ctx.dataset.label === 'Spike') return '⚡ Traffic spike';
                            return ctx.dataset.label + ': ' + Number(ctx.parsed.y).toFixed(3) + ' Mbps';
                        }
                    }
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        drag: {
                            enabled: true
                        },
                        mode: 'xy',
                    },
                    pan: {
                        enabled: false,
                        mode: 'y',
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'hour',
                        tooltipFormat: 'YYYY-MM-DD HH:mm:ss',
                        displayFormats: {
                            hour: 'H a'
                        }
                    },
                    title: {
                        display: false,
                        text: 'Timestamp'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Mbps'
                    },
                    min: 0
                }
            }
        }
    }); //end create chart
    window[chartName] = myChart;
}


/**
 * Renders a line chart displaying Uptime data.
 *
 * Original: y-axis fixed 0–100; no dynamic title; point markers on every sample.
 * Enhanced: y-axis min set just below the data minimum so small dips are visible;
 * title dynamically includes the average uptime %; point markers removed for a
 * cleaner line; downtime event markers removed per client request.
 *
 * @param {string} data - The average uptime data in JSON format.
 * @param {CanvasRenderingContext2D} ctx - The rendering context for the chart.
 * @param {string} chartName - The global window key to store the chart instance.
 * @return {void}
 */
function renderUptimeChart(data, ctx, chartName) {

    data = JSON.parse(data);
    console.log("converting data to float");
    console.log(data);
    const numericData = data.series.map(parseFloat);

    const reversedData   = numericData.reverse();        // Reverse the data series to match the labels
    const labelsReversed = data.labels.reverse();        // Reverse the labels to maintain chronological order

    // Compute average uptime for the dynamic chart title
    const avg = (reversedData.reduce((a, b) => a + b, 0) / reversedData.length).toFixed(1);

    // Set y-axis minimum just below the lowest value so small dips are visible.
    // Clamps to 0 so the axis never goes negative.
    const minVal = Math.min(...reversedData);
    const yMin   = Math.max(0, Math.floor(minVal - 5));

    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labelsReversed,
            datasets: [
                {
                    label: 'Average Uptime',
                    data: reversedData,
                    fill: true,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.4,
                    pointRadius: 0  // Hidden for a cleaner line at high sample density
                },
            ]
        },
        options: {
            responsive: true,
            // maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: `Average Uptime (last 24 hours) — avg ${avg}%`
                },
                tooltip: {
                    callbacks: {
                        label: ctx => 'Uptime: ' + Number(ctx.parsed.y).toFixed(1) + '%'
                    }
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: false,
                        },
                        drag: {
                            enabled: false
                        },
                        mode: 'xy',
                    },
                    pan: {
                        enabled: false,
                        mode: 'y',
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'hour',
                        tooltipFormat: 'YYYY-MM-DD HH:mm:ss',
                        displayFormats: {
                            hour: 'H a'
                        }
                    },
                    title: {
                        display: false,
                        text: 'Timestamp'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Uptime %'
                    },
                    min: yMin,  // Dynamic minimum — shows dips clearly instead of fixed 0
                    max: 100
                }
            }
        }
    }); //end create chart
    window[chartName] = myChart;
}



/**
 * Draws Signal Bars in the given canvas element.
 * @param {string} canvasId the target canvas element
 * @param {integer} numBars the number of bars to draw
 * @param {integer} maxBars the maximum number of bars
 */
function drawSignalBars(canvasId, numBars, maxBars, barColor='green') {
    maxBars = maxBars + 1;
    var canvas = document.getElementById(canvasId);
    var ctx = canvas.getContext("2d");
  
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  
    // Get the actual width of the canvas element
    var canvasWidth = canvas.offsetWidth;
  
    // Calculate bar width based on maxBars and canvas width
    var barWidth = canvasWidth / (maxBars + 1); // Adjust for spacing between bars
  
    // Calculate spacing based on canvas width, bar width, and maxBars
    var spacing = (canvasWidth - maxBars * barWidth) / (maxBars + 1);
  
    // Calculate the maximum possible height based on canvas height and maxBars
    var maxHeight = canvas.offsetHeight / (maxBars * (maxBars + 1) / 2); 
  
    for (var i = 0; i <= numBars; i++) {
      ctx.beginPath();
      var x = spacing + i * (barWidth + spacing);
      var y = canvas.height;
      var barHeight = maxHeight * (i * (i + 1)) / 2; // Calculate height based on loop counter
  
      ctx.rect(x, y - barHeight, barWidth, barHeight);
      ctx.fillStyle = barColor; // Set fill style for solid color
      ctx.fill();
    }
  }
