/**
 * Author: Ely Millan <eleuteriomillanjr@@gmail.com>
 * Date: 2023-06-14
 * Description: This file contains the code for the router details page.
 *
 * Enhanced by: Claude (Anthropic)
 * Date: 2026-04-30
 * Changes:
 *   - renderBandwidthChart: switched from line to bar chart for clearer per-sample
 *     visibility; spike detection changed from 3x median to 95th percentile threshold
 *     (more accurate for bursty Starlink data); y-axis max capped at p95x1.5 so the
 *     baseline stays readable while spikes remain inspectable via zoom; pinch-to-zoom
 *     and pan enabled for touch devices; metric cards use rgba backgrounds and borders
 *     for dark/light mode compatibility.
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
 * Enhanced: switched to bar chart; spikes auto-detected at the 95th percentile
 * (more accurate than 3x median for bursty Starlink data); y-axis max capped at
 * the 95th percentile value x1.5 so the baseline is readable — large spikes are
 * still visible but don't squash everything else; pinch-to-zoom and pan enabled
 * for touch devices; metric cards use rgba for dark mode compatibility.
 *
 * @param {string} data - The bandwidth data in JSON format.
 * @param {CanvasRenderingContext2D} ctx - The rendering context for the chart.
 * @param {string} chartName - The global window key to store the chart instance.
 * @return {void}
 */
function renderBandwidthChart(data, ctx, chartName, rangeLabel, xAxis) {

    data = JSON.parse(data);
    const downlinkThroughputMbps = data.data_series.downlinkThroughputBps.map(convertBpsToMbps);
    const uplinkThroughputMbps = data.data_series.uplinkThroughputBps.map(convertBpsToMbps);

    const dlReversed     = downlinkThroughputMbps.reverse(); // Reverse the data series to match the labels
    const ulReversed     = uplinkThroughputMbps.reverse();   // Reverse the data series to match the labels
    const labelsReversed = data.labels.reverse();            // Reverse the labels to maintain chronological order


    // Compute summary values for the metric cards
    const peakDl = Math.max(...dlReversed).toFixed(3);
    const avgDl  = (dlReversed.reduce((a, b) => a + b, 0) / dlReversed.length).toFixed(3);
    const peakUl = Math.max(...ulReversed).toFixed(3);

    // Inject summary metric cards above the chart (idempotent — skipped if already present).
    // Detects dark mode via the page's dark class or prefers-color-scheme media query
    // and applies appropriate background, border, and text colours for each mode.
    const canvas   = ctx.canvas;
    const wrapper  = canvas.closest('.chart-container') || canvas.parentElement;
    if (!wrapper.parentElement.querySelector('.p2p-bw-metrics')) {
        // Use Tailwind classes matching the rest of the template (dark: variants handled by Tailwind)
        const metricsHtml = `
        <div class="p2p-bw-metrics grid grid-cols-3 gap-3 mb-3">
            <div class="rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Peak download</div>
                <div class="text-lg font-medium" style="color:#1D9E75;">${peakDl} <span class="text-xs font-normal text-gray-500 dark:text-gray-400">Mbps</span></div>
            </div>
            <div class="rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg download</div>
                <div class="text-lg font-medium text-gray-800 dark:text-gray-200">${avgDl} <span class="text-xs font-normal text-gray-500 dark:text-gray-400">Mbps</span></div>
            </div>
            <div class="rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Peak upload</div>
                <div class="text-lg font-medium" style="color:#9f97e8;">${peakUl} <span class="text-xs font-normal text-gray-500 dark:text-gray-400">Mbps</span></div>
            </div>
        </div>`;
        wrapper.insertAdjacentHTML('beforebegin', metricsHtml);

        // Zoom preset buttons — visible only on Per-Minute tab, hidden on Real-Time
        // Each button narrows the x-axis window without re-fetching data
        if (!wrapper.parentElement.querySelector('.p2p-zoom-presets')) {
            const zoomHtml = `
            <div class="p2p-zoom-presets hidden flex items-center gap-2 mb-3 text-sm">
                <span class="text-gray-500 dark:text-gray-400 text-xs">Zoom</span>
                <button class="p2p-zoom-btn btn btn-sm border-primary text-primary hover:bg-primary hover:text-white" data-hours="1">1 Hour</button>
                <button class="p2p-zoom-btn btn btn-sm border-primary text-primary hover:bg-primary hover:text-white" data-hours="3">3 Hours</button>
                <button class="p2p-zoom-btn btn btn-sm border-primary text-primary hover:bg-primary hover:text-white" data-hours="6">6 Hours</button>
                <button class="p2p-zoom-btn btn btn-sm border-primary text-primary hover:bg-primary hover:text-white" data-hours="12">12 Hours</button>
                <button class="p2p-zoom-btn btn btn-sm border-primary text-primary hover:bg-primary hover:text-white" data-hours="24">All</button>
            </div>`;
            wrapper.insertAdjacentHTML('beforebegin', zoomHtml);

            // Wire up zoom preset buttons — shift x-axis min without re-fetching
            wrapper.parentElement.querySelectorAll('.p2p-zoom-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    wrapper.parentElement.querySelectorAll('.p2p-zoom-btn').forEach(b =>
                        b.classList.remove('bg-primary', 'text-white'));
                    this.classList.add('bg-primary', 'text-white');
                    const hours = parseFloat(this.dataset.hours);
                    const chart = window[chartName];
                    if (!chart) return;
                    const now = new Date();
                    chart.options.scales.x.min = new Date(now.getTime() - hours * 3600000).toISOString();
                    chart.options.scales.x.max = now.toISOString();
                    chart.update();
                });
            });
        }
    }

    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labelsReversed,
            datasets: [
                {
                    label: 'Download',
                    data: dlReversed,
                    backgroundColor: 'rgba(29,158,117,0.15)',
                    borderColor: '#1D9E75',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: true,
                    tension: 0.3,
                    order: 1
                },
                {
                    label: 'Upload',
                    data: ulReversed,
                    backgroundColor: 'rgba(153, 102, 255, 0.1)',
                    borderColor: 'rgba(153, 102, 255, 0.8)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: true,
                    tension: 0.3,
                    order: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Bandwidth (DL/UL)' + (rangeLabel ? ' — ' + rangeLabel : '')
                },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            if (ctx.dataset.label === 'Spike') return '⚡ Traffic spike';
                            return ctx.dataset.label + ': ' + Number(ctx.parsed.y).toFixed(3) + ' Mbps';
                        }
                    }
                },
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: (xAxis && xAxis.unit) || 'hour',
                        tooltipFormat: 'YYYY-MM-DD HH:mm:ss',
                        displayFormats: {
                            minute: (xAxis && xAxis.displayFormat) || 'HH:mm',
                            hour:   (xAxis && xAxis.displayFormat) || 'H a',
                            day:    (xAxis && xAxis.displayFormat) || 'MMM D',
                            week:   (xAxis && xAxis.displayFormat) || 'MMM D',
                        }
                    },
                    ticks: {
                        stepSize: (xAxis && xAxis.stepSize) || 1,
                        maxRotation: 45,
                        autoSkip: false,
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
 * Original: y-axis fixed 0-100; no dynamic title; point markers on every sample.
 * Enhanced: y-axis min set just below the data minimum so small dips are visible;
 * title dynamically includes the average uptime %; point markers removed for a
 * cleaner line; downtime event markers removed per client request.
 *
 * @param {string} data - The average uptime data in JSON format.
 * @param {CanvasRenderingContext2D} ctx - The rendering context for the chart.
 * @param {string} chartName - The global window key to store the chart instance.
 * @return {void}
 */
function renderUptimeChart(data, ctx, chartName, rangeLabel, xAxis) {

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
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: `Average Uptime${rangeLabel ? " — " + rangeLabel : ""} — avg ${avg}%`
                },
                tooltip: {
                    callbacks: {
                        label: ctx => 'Uptime: ' + Number(ctx.parsed.y).toFixed(1) + '%'
                    }
                },
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: (xAxis && xAxis.unit) || 'hour',
                        tooltipFormat: 'YYYY-MM-DD HH:mm:ss',
                        displayFormats: {
                            minute: (xAxis && xAxis.displayFormat) || 'HH:mm',
                            hour:   (xAxis && xAxis.displayFormat) || 'H a',
                            day:    (xAxis && xAxis.displayFormat) || 'MMM D',
                            week:   (xAxis && xAxis.displayFormat) || 'MMM D',
                        }
                    },
                    ticks: {
                        stepSize: (xAxis && xAxis.stepSize) || 1,
                        maxRotation: 45,
                        autoSkip: false,
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


/**
 * Initialises the Realtime / Hourly / Daily / Monthly tab bar for both the
 * bandwidth and uptime Starlink charts.
 *
 * Added by: Claude (Anthropic) — 2026-04-30
 *
 * How it works:
 *   - Each tab computes a start_date / end_date window and fires a fresh AJAX
 *     request to the existing StarlinkDataView endpoint (same URL, extra params).
 *   - The existing chart instance is destroyed before re-rendering so Chart.js
 *     doesn't complain about canvas reuse.
 *   - Realtime tab auto-refreshes every 60 seconds using setInterval; switching
 *     away from Realtime clears the interval.
 *   - A small "● Live" badge next to the tabs is shown only in Realtime mode.
 *
 * @param {number} idx            - Starlink interface index (from Django forloop)
 * @param {string} bwUrl          - URL for bandwidth chart data endpoint
 * @param {string} uptimeUrl      - URL for uptime chart data endpoint
 */
function initStarlinkTabs(idx, bwUrl, uptimeUrl) {

    // Map tab → hours of data to fetch from the backend
    const rangeHours = {
        realtime: 0.25,  // 15 minutes — live ticker
        hourly:   24,    // full day per-minute report
    };

    // Human-readable label shown in the chart title per tab
    const rangeLabels = {
        realtime: 'Real-Time (last 15 min)',
        hourly:   'Per-Minute Report (last 24 hours)',
    };

    // x-axis time unit/format per tab
    const rangeXAxis = {
        realtime: { unit: 'minute', stepSize: 1,  displayFormat: 'HH:mm' },
        hourly:   { unit: 'minute', stepSize: 15, displayFormat: 'HH:mm' },
    };

    // Track the realtime auto-refresh intervals so we can clear them on tab switch
    let bwInterval     = null;
    let uptimeInterval = null;

    /**
     * Returns ISO-formatted start/end date strings for a given range key.
     * @param {string} range
     * @returns {{ start_date: string, end_date: string }}
     */
    function getDateParams(range) {
        const now   = new Date();
        const start = new Date(now.getTime() - rangeHours[range] * 60 * 60 * 1000);
        return {
            start_date: start.toISOString().slice(0, 19).replace('T', ' '),
            end_date:   now.toISOString().slice(0, 19).replace('T', ' '),
        };
    }

    /**
     * Fetches bandwidth data for the given range and re-renders the chart.
     * Destroys any existing chart instance first.
     * @param {string} range
     */
    function loadBandwidth(range) {
        const chartName = 'starlinkBandwidthChart' + idx;
        if (window[chartName]) {
            window[chartName].destroy();
            window[chartName] = null;
        }
        $.ajax({
            url: bwUrl,
            type: 'GET',
            data: Object.assign({ interface_index: idx }, getDateParams(range)),
            success: function(data) {
                const ctx = document.getElementById('starlink-bandwidth-chart-' + idx).getContext('2d');
                renderBandwidthChart(data, ctx, chartName, rangeLabels[range], rangeXAxis[range]);
            },
            error: function(xhr, status, error) {
                console.error('Bandwidth AJAX Error:', status, error);
            }
        });
    }

    /**
     * Fetches uptime data for the given range and re-renders the chart.
     * Destroys any existing chart instance first.
     * @param {string} range
     */
    function loadUptime(range) {
        const chartName = 'starlinkUptimeChart' + idx;
        if (window[chartName]) {
            window[chartName].destroy();
            window[chartName] = null;
        }
        $.ajax({
            url: uptimeUrl,
            type: 'GET',
            data: Object.assign({ interface_index: idx }, getDateParams(range)),
            success: function(data) {
                const ctx = document.getElementById('starlink-uptime-chart-' + idx).getContext('2d');
                renderUptimeChart(data, ctx, chartName, rangeLabels[range], rangeXAxis[range]);
            },
            error: function(xhr, status, error) {
                console.error('Uptime AJAX Error:', status, error);
            }
        });
    }

    /**
     * Wires up a set of tab buttons for a single chart type (bandwidth or uptime).
     * @param {string} chartType  - 'bandwidth' | 'uptime'
     * @param {Function} loadFn   - loadBandwidth or loadUptime
     */
    function bindTabs(chartType, loadFn) {
        // Find this chart's tab bar using data attributes set in the template
        const tabBar  = $('[data-chart-index="' + idx + '"][data-chart-type="' + chartType + '"]');
        const buttons = tabBar.find('.starlink-tab-btn');
        const badge   = tabBar.find('.starlink-realtime-badge');

        if (!tabBar.length) {
            console.warn('initStarlinkTabs: no tab bar found for', chartType, 'index', idx);
            return;
        }

        // Track the interval local to this chart type
        let liveInterval = null;

        buttons.on('click', function() {
            const range = $(this).data('range');

            // Update active styling
            buttons.removeClass('active bg-primary text-white').addClass('text-primary');
            $(this).addClass('active bg-primary text-white').removeClass('text-primary');

            // Show/hide live badge
            if (range === 'realtime') {
                badge.removeClass('hidden');
            } else {
                badge.addClass('hidden');
            }

            // Clear any existing auto-refresh
            if (liveInterval) {
                clearInterval(liveInterval);
                liveInterval = null;
            }

            // Load data immediately
            loadFn(range);

            // Show zoom preset buttons only on Per-Minute (hourly) bandwidth tab.
            // Scope lookup to the bandwidth card only using the canvas ID, not closest().
            if (chartType === 'bandwidth') {
                const bwCanvas  = document.getElementById('starlink-bandwidth-chart-' + idx);
                const bwCard    = bwCanvas ? bwCanvas.closest('.card') : null;
                const zoomBar   = bwCard ? bwCard.querySelector('.p2p-zoom-presets') : null;
                if (zoomBar) {
                    if (range === 'hourly') {
                        zoomBar.classList.remove('hidden');
                        const defaultBtn = zoomBar.querySelector('[data-hours="1"]');
                        if (defaultBtn) setTimeout(() => defaultBtn.click(), 300);
                    } else {
                        zoomBar.classList.add('hidden');
                    }
                }
            }

            // For realtime, set up auto-refresh every 60 seconds
            if (range === 'realtime') {
                liveInterval = setInterval(function() {
                    loadFn('realtime');
                }, 60000);
            }
        });

        // Trigger realtime on load
        buttons.filter('[data-range="realtime"]').trigger('click');
    }

    bindTabs('bandwidth', loadBandwidth);
    bindTabs('uptime',    loadUptime);
}
