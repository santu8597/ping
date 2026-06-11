//For downloading the json
function downloadJSON() {
    if (!window.dnsData) {
        alert("Data not found!");
        return;
    }
    //const data = JSON.parse(`{{ json_data|escapejs }}`);
    const json = JSON.stringify(window.dnsData, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const link = document.getElementById("exportJson");
    link.href = url;
    link.download = "dnsquery_" + window.historyId + ".json";
}


//For downloading the csv
 //const dnsData = JSON.parse(`{{ json_data|escapejs }}`);
    const dnsData = window.dnsData;
    function extractServerData(section, source) {
      const servers = section?.servers || [];
      const data = [];

      servers.forEach(entry => {
        const serverName = Object.keys(entry)[0];
        const details = entry[serverName];

        data.push({
          source: source,
          server_name: serverName,
          ip: details.ip || '',
          query_time: details.query_time || '',
          is_authority: details.is_authority || '',
          type: details.type || '',
          rtt: details.rtt || '',
          rtt_ms: details.rtt_ms || '',
          answer: Array.isArray(details.answer) ? details.answer.join('; ') : (details.answer || '')
        });
      });

      return data;
    }

    function convertToCSV(rows) {
      const headers = Object.keys(rows[0]);
      const csvRows = [
        headers.join(','), // header row
        ...rows.map(row => headers.map(header => `"${(row[header] ?? '')}"`).join(','))
      ];
      return csvRows.join('\n');
    }

    function downloadCSV() {
      const rootRows = extractServerData(dnsData.root_data, 'root');
      const domainRows = extractServerData(dnsData.domain_data, 'domain');
      const tldRows = extractServerData(dnsData.tld_data, 'tld');

      const allRows = [...rootRows, ...domainRows, ...tldRows];
      if (allRows.length === 0) {
        alert('No data to export.');
        return;
      }

      const csv = convertToCSV(allRows);
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.setAttribute('href', url);
      //a.setAttribute('download', 'dns_query_'+`{{ history_id|safe }}`+'.csv');
        a.setAttribute('download', 'dns_query_'+ window.historyId +'.csv');
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

     function printScreen() {
    window.print();
}

//downloading authoritative graph
 function downloadChart1() {
        const chartContainer = document.getElementById("chart1")

        html2canvas(chartContainer).then(canvas => {
            const link = document.createElement("a");
           // link.download = "chart_"+"authoritative_"+`{{ history_id|safe }}`+".png";
             link.download = "chart_"+"authoritative_"+window.historyId+".png";
            link.href = canvas.toDataURL("image/png");
            link.click();
        });
    }
  //  downloading tld graph
 function downloadChart2() {
        const chartContainer = document.getElementById("chart2")

        html2canvas(chartContainer).then(canvas => {
            const link = document.createElement("a");
            link.download = "chart_"+"tld_"+window.historyId+".png";
            link.href = canvas.toDataURL("image/png");
            link.click();
        });
    }
      //  downloading root graph
 function downloadChart3() {
         const chartContainer = document.getElementById("chart3")

        html2canvas(chartContainer).then(canvas => {
            const link = document.createElement("a");
            link.download = "chart_"+"root_"+window.historyId+".png";
            link.href = canvas.toDataURL("image/png");
            link.click();
        });

 }

        $("#link_btn").on("click", function () {
         let assignment = $("#assignment").val();
         let commandName = $("#commandName").val();
         let query_id = $("#query_id").val();
         let assignment_remarks = $("#assignment_remarks").val();
         if (!assignment) {
            alert("Please Enter Assignment Name!");
            return;
        }
         mydata = {
             "assignment": assignment,
             "command":commandName,
             "query_id":query_id,
             "assignment_remarks":assignment_remarks,
             "assignment_query_type": "",
             "assignment_zone": ""
         }
               $.ajax({
                url: `/link-query/`,
                method: "POST",
                headers: {'X-CSRFToken': document.getElementById('csrf').querySelector('input').value},
                data: mydata,
                success: function (response) {
                    if (response.status == 1) {
                         Swal.fire({
                            title: 'Success!',
                            text: 'Query Linked to Assignment Successfully',
                            icon: 'success',
                            confirmButtonText: 'OK'
                        }).then(() => {
                             location.reload();
                        });
                    } else {
                        showError(response.error || "Failed to link query to assignment!");
                    }
                },
                error: function () {
                    showError("Something went wrong! Please try again.");
                }
            });
          });
 // Show Error Inside Modal
    function showError(message) {
        Swal.fire({
            icon: "error",
            title: "Error",
            text: message,
            confirmButtonColor: "#d33"
        });
    }