
/**
 * Used in conjuction with `job_result_modal` to pop up the modal, start the job, provide progress spinner, 
 * provide job status, job results link, redirect link, and error message.
 *
 * @requires nautobot_csrf_token - The CSRF token obtained from Nautobot.
 * @param {string} jobClass - The jobs `class_path` as defined on the job detail page.
 * @param {Object} data - The object containing payload data to send to the job.
 * @param {string} redirectUrlTemplate - The redirect url to provide, you have access to jobData with the syntax like `{jobData.someKey}`, leave `undefined` if none is required.
 * @param {string} callBack - The promise function to return the success or failure message, leave `undefined` no callback is required.
 */
function startJob(jobClass, data, redirectUrlTemplate, callBack) {
  var jobApi = `/api/extras/jobs/${jobClass}/run/`;

  if (typeof callBack === "undefined") {
    var callBack = getMessage;
  }

  $.ajax({
      type: 'POST',
      url: jobApi,
      contentType: "application/json",
      data: JSON.stringify(data),
      dataType: 'json',
      headers: {
          'X-CSRFToken': nautobot_csrf_token
      },
      beforeSend: function() {
          // Normalize to base as much as you can.
          $('#jobStatus').html("Pending").show();
          $('#loaderImg').show();
          $('#jobResults').hide();
          $('#redirectLink').hide();
          $('#detailMessages').hide();
        },
      success: function(jobData) {
          $('#jobStatus').html("Started").show();
          var jobResultUrl = "/extras/job-results/" + jobData.result.id + "/";
          $('#jobResults').html(iconLink(jobResultUrl, "mdi-open-in-new", "Job Details")).show();
          pollJobStatus(jobData.result.url, callBack);
          if (typeof redirectUrlTemplate !== "undefined") {
            var redirectUrl = _renderTemplate(redirectUrlTemplate, jobData);
            $('#redirectLink').html(iconLink(redirectUrl, "mdi-open-in-new", "Info"));
          }
      },
      error: function(e) {
          $("#loaderImg").hide();
          console.log("There was an error with your request...");
          console.log("error: " + JSON.stringify(e));
          $('#jobStatus').html("Failed").show();
          $('#detailMessages').show();
          $('#detailMessages').attr('class', 'alert alert-danger text-center');
          $('#detailMessages').html("<b>Error: </b>" + e.responseText);
      }
  });
}

/**
* Polls the status of a job with the given job ID.
*
* This function makes an AJAX request to the server,
* to get the current status of the job with the specified job ID.
* It continues to poll the status until the job completes or fails.
* The job status is updated in the HTML element with ID 'jobStatus'.
* If the job encounters an error, additional error details are shown.
* The call is not made async, so that the parent call will wait until
* this is completed.
*
* @requires nautobot_csrf_token - The CSRF token obtained from Nautobot.
* @param {string} jobId - The ID of the job to poll.
* @returns {void}
*/
function pollJobStatus(jobId, callBack) {
$.ajax({
  url: jobId,
  type: "GET",
  async: false,
  dataType: "json",
  headers: {
    'X-CSRFToken': nautobot_csrf_token
  },
  success: function (data) {
    $('#jobStatus').html(data.status.value.charAt(0).toUpperCase() + data.status.value.slice(1)).show();
    if (["errored", "failed"].includes(data.status.value)) {
      $("#loaderImg").hide();
      $('#detailMessages').show();
      $('#detailMessages').attr('class', 'alert alert-warning text-center');
      $('#detailMessages').html("Job started but failed during the Job run. This job may have partially completed. See Job Results for more details on the errors.");
    } else if (["running", "pending"].includes(data.status.value)) {
      // Job is still processing, continue polling
      setTimeout(function () {
        pollJobStatus(jobId, callBack);
      }, 1000); // Poll every 1 seconds
    } else if (data.status.value == "completed") {
      $("#loaderImg").hide();
      $('#detailMessages').show();
      callBack(data.id)
        .then((message) => {
          $('#redirectLink').show();
          $('#detailMessages').attr('class', 'alert alert-success text-center');
          $('#detailMessages').html(message)
        })
        .catch((message) => {
          $('#detailMessages').attr('class', 'alert alert-warning text-center');
          $('#detailMessages').html(message)
        })
    }
  },
      error: function(e) {
        $("#loaderImg").hide();
        console.log("There was an error with your request...");
        console.log("error: " + JSON.stringify(e));
        $('#detailMessages').show();
        $('#detailMessages').attr('class', 'alert alert-danger text-center');
        $('#detailMessages').html("<b>Error: </b>" + e.responseText);
      }
    })
};
/**
* Converts a list of form data objects to a dictionary.
*
* @param {FormData} formData - The form data object to be converted.
* @param {string[]} listKeys - The list of keys for which values should be collected as lists.
* @returns {Object} - The dictionary representation of the form data.
*/
function formDataToDictionary(formData, listKeys) {
const dict = {};

formData.forEach(item => {
  const { name, value } = item;
  if (listKeys.includes(name)) {
    if (!dict[name]) {
      dict[name] = [value];
    } else {
      dict[name].push(value);
    }
  } else {
    dict[name] = value;
  }
});

return dict;
}

/**
* Generates an HTML anchor link with an icon.
*
* @param {string} url - The URL to link to.
* @param {string} icon - The name of the Material Design Icon to use.
* @param {string} title - The title to display when hovering over the icon.
* @returns {string} - The HTML anchor link with the specified icon.
*/
function iconLink(url, icon, title) {

const linkUrl = `<a href="${url}" target="_blank">` + 
`  <span class="text-primary">` +
`    <i class="mdi ${icon}" title="${title}"></i>` +
`  </span>` +
`</a>`
return linkUrl
}

/**
* Renders a template string with placeholders replaced by corresponding values from jobData.
*
* @param {string} templateString - The template string with placeholders in the form of `{jobData.someKey}`.
* @param {Object} jobData - The object containing data to replace placeholders in the template.
* @returns {string} - The rendered string with placeholders replaced by actual values from jobData.
*/
function _renderTemplate(templateString, data) {
// Create a regular expression to match placeholders in the template
const placeholderRegex = /\{jobData\.([^\}]+)\}/g;

// Replace placeholders with corresponding values from jobData
const renderedString = templateString.replace(placeholderRegex, (match, key) => {
  const keys = key.split(".");
  let value = data;
  for (const k of keys) {
    if (value.hasOwnProperty(k)) {
      value = value[k];
    } else {
      return match; // If the key is not found, keep the original placeholder
    }
  }
  return value;
});

return renderedString;
}

function getMessage(jobResultId) {
return new Promise((resolve) => {
    resolve("Job Completed Successfully.");
});
}
