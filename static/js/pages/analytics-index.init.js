// Check if the chartData object is defined
if (window.chartData) {

    const totalPoints = window.chartData.totalPoints;
    const remainingPoints = window.chartData.remainingPoints;
    const usedPoints = window.chartData.usedPoints;

    // Chart configuration for the donut chart
    var optionsDonut = {
        chart: { height: 255, type: "donut" },
        plotOptions: { pie: { donut: { size: "85%" } } },
        dataLabels: { enabled: false },
        stroke: { show: true, width: 2, colors: ["transparent"] },
        // series: [totalPoints, remainingPoints, usedPoints], // Use the data from Django
        series: [remainingPoints, usedPoints], // Use the data from Django
        legend: {
            show: true,
            position: "bottom",
            horizontalAlign: "center",
            verticalAlign: "middle",
            floating: false,
            fontSize: "13px",
            offsetX: 0,
            offsetY: 0
        },
        // labels: ["Total Points", "Remaining Points", "Used Points"],
        labels: ["Remaining Points", "Used Points"],
        // colors: ["#2a76f4", "rgba(42, 118, 244, .5)", "rgba(42, 118, 244, .18)"],
        colors: ["#2a76f4", "rgba(42, 118, 244, .5)",],
        responsive: [{
            breakpoint: 600,
            options: {
                plotOptions: { donut: { customScale: 0.2 } },
                chart: { height: 240 },
                legend: { show: false }
            }
        }],
        tooltip: { y: { formatter: function (t) { return t + " "; } } }
    };

    // Create the donut chart
    var chartDonut = new ApexCharts(document.querySelector("#ana_device"), optionsDonut);
    chartDonut.render();
} else {
    console.error('chartData is undefined. Please check your template.');
}










var options = {
    series: [{
        name: "New Visitors",
        data: [68, 44, 55, 57, 56, 61, 58, 63, 60, 66]
    }, {
        name: "Unique Visitors",
        data: [51, 76, 85, 101, 98, 87, 105, 91, 114, 94]
    }],
    chart: {
        height: 330,
        type: "bar",
        toolbar: { show: false }
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: "20%",
            endingShape: "rounded",
            barCap: "round"
        }
    },
    dataLabels: { enabled: false },
    stroke: { show: true, width: 2, colors: ["transparent"] },
    colors: ["#1ccab8", "#2a76f4"],
    xaxis: {
        categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"],
        axisBorder: { show: true, color: "#bec7e0" },
        axisTicks: { show: true, color: "#bec7e0" }
    },
    yaxis: { title: { text: "Visitors" } },
    fill: { opacity: 1 },
    grid: { row: { colors: ["transparent", "transparent"], opacity: 0.2 }, strokeDashArray: 2.5 },
    tooltip: { y: { formatter: function (t) { return t + "k"; } } }
};

var chartMain = new ApexCharts(document.querySelector("#ana_dash_1"), options);
chartMain.render();

// Function to generate random data for the bar chart
function generateRandomData() {
    return Array.from({ length: 10 }, () => Math.floor(Math.random() * 100));
}

// Update the bar chart every 5 seconds
setInterval(function () {
    chartMain.updateSeries([{
        name: "New Visitors",
        data: generateRandomData()
    }, {
        name: "Unique Visitors",
        data: generateRandomData()
    }]);
}, 5000);
