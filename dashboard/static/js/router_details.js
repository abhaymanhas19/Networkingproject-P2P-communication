/**
 * Author: Ely Millan <eleuteriomillanjr@@gmail.com>
 * Date: 2023-06-14
 * Description: This file contains the code for the router details page.
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
 * Renders a line chart displaying bandwidth data.
 *
 * @param {string} data - The bandwidth data in JSON format.
 * @param {CanvasRenderingContext2D} ctx - The rendering context for the chart.
 * @return {Chart} The rendered line chart.
 */
function  renderBandwidthChart(data, ctx, chartName){

    data = JSON.parse(data)
    const downlinkThroughputMbps = data.data_series.downlinkThroughputBps.map(convertBpsToMbps);
    const uplinkThroughputMbps = data.data_series.uplinkThroughputBps.map(convertBpsToMbps);
    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels.reverse(), // Reverse the labels to maintain chronological order
            datasets: [
                {
                    label: 'Download',
                    data: downlinkThroughputMbps.reverse(), // Reverse the data series to match the labels
                    fill: true,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.4
                },
                {
                    label: 'Upload',
                    data: uplinkThroughputMbps.reverse(), // Reverse the data series to match the labels
                    fill: true,
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    tension: 0.4
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
                    }
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
function drawSignalBars(canvasId, numBars, maxBars) {
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
      ctx.fillStyle = "green"; // Set fill style for solid color
      ctx.fill();
    }
  }