
// Header Scripts
$(document).ready(function() {
    $('#update-device-alias-form').submit(function(event) {
        event.preventDefault();
        var aliasValue = $('#device-alias-value').val();
        $.ajax({
            url: '/set_alias',
            method: 'POST',
            data: {
                'device-alias-value': aliasValue
            },
            success: function(response) {
                if (response.success) {
                    $('#device-alias').text('Device Alias: ' + response.alias);
                }
            },
            error: function() {
                alert('Error updating alias.');
            }
        });
    });
});

$('#filter-btn').click(function() {
    $.ajax({
        url: '/set_filter',
        type: 'POST',
        success: function(response) {
            $('#filter-ts').text('Last Filter Change: ' + response.filter_ts);
            $('#water-ts').text('Last Water Swap: ' + response.water_ts);
        },
        error: function(xhr, status, error) {
            alert("There was an error updating the filter change time.");
        }
    });
});
$('#water-btn').click(function() {
    $.ajax({
        url: '/set_water',
        type: 'POST',
        success: function(response) {
            $('#filter-ts').text('Last Filter Change: ' + response.filter_ts);
            $('#water-ts').text('Last Water Swap: ' + response.water_ts);
        },
        error: function(xhr, status, error) {
            alert("There was an error updating the water swap time.");
        }
    });
});
$('#feeder-btn').click(function() {
    var selectedInterval = $('input[name="interval"]:checked').val();
    var interval = selectedInterval ? selectedInterval : '0';

    $.ajax({
        url: '/set_feeder',
        type: 'POST',
        data: {
            interval: interval
        },
        /* Debug Alerts */
        // success: function(response) {
        //     // Feed now action completed
        //     alert("Feeding done!");
        // },
        // error: function(xhr, status, error) {
        //     alert("There was an error processing the feed request.");
        // }
    });
});
$('#update-interval-btn').click(function() {
    var selectedInterval = $('input[name="interval"]:checked').val();
    var interval = selectedInterval ? selectedInterval : '0';

    $.ajax({
        url: '/set_feed_interval',
        type: 'POST',
        data: {
            interval: interval
        },
        /* Debug Alerts */
        // success: function(response) {
        //     alert("Interval updated successfully!");
        // },
        // error: function(xhr, status, error) {
        //     alert("There was an error updating the interval.");
        // }
    });
});

// Media Scripts

let videoPlayer = document.getElementById("media-video-player");
let imageContainer = document.getElementById("media-image-container");
let mediaRadioButtons = document.querySelectorAll('.media-radio');

const socket = io();

socket.on('connect', () => {
    setStatus('connected');
});

socket.on('frame', (jpg_as_text) => {
    const img = document.getElementById('media-video-source');
    img.src = 'data:image/jpeg;base64,' + jpg_as_text;
});

socket.on('disconnect', () => {
    setStatus('disconnected');
});

function setStatus(status) {
    const statusText = document.getElementById('status-text');
    statusText.textContent = status;
    if (status === 'connected') {
        statusText.classList.remove('status-disconnected');
        statusText.classList.add('status-connected');
        statusText.textContent = 'connected';
    } else {
        statusText.classList.remove('status-connected');
        statusText.classList.add('status-disconnected');
        statusText.textContent = 'disconnected';
    }
}

function changeMedia() {
    let selectedMedia = document.querySelector('input[name="media-toggle"]:checked').value;

    if (selectedMedia === 'video') {
        imageContainer.classList.remove("active");
        videoPlayer.classList.add("active");


    } else if (selectedMedia === 'image') {
        videoPlayer.classList.remove("active");
        imageContainer.classList.add("active");

        fetchLatestHeatmap();
    }
}

function fetchLatestHeatmap() {
    $.ajax({
        url: '/get_heatmap',
        method: 'GET',
        success: function(data) {
            const imageElement = document.querySelector('#media-image-container img');
            imageElement.src = data.latest_image;
        },
        error: function() {
            console.error('Error fetching the latest heatmap.');
        }
    });
}

mediaRadioButtons.forEach(function(radio) {
    radio.addEventListener('change', changeMedia);
});

changeMedia();

// Vitals Scripts
$(document).ready(function() {
    function fetchLatestData() {
        $.ajax({
            type: 'GET',
            url: '/get_vitals',
            success: function(response) {
                document.getElementById('temp-reported').textContent = 'Reported: ' + (response.latest_temp.reported_value || 'N/A') + ' °F';
                document.getElementById('ph-reported').textContent = 'Reported: ' + (response.latest_ph.reported_value || 'N/A') + ' pH';
                document.getElementById('do-reported').textContent = 'Reported: ' + (response.latest_do.reported_value || 'N/A') + ' ppm';
            },
            error: function() {
                console.error('Error fetching latest data.');
            }
        });
    }
    fetchLatestData();
    setInterval(fetchLatestData, 1000);

    $('#set-values-form').on('submit', function(event) {
        event.preventDefault();
        $.ajax({
            type: 'POST',
            url: '/set_vitals',
            data: $(this).serialize(),
            cache: false,
            success: function(response) {
                $('#temp-set').text('Set: ' + response.latest_temp.set_value + ' °F');
                $('#ph-set').text('Set: ' + response.latest_ph.set_value + ' pH');
                $('#do-set').text('Set: ' + response.latest_do.set_value + ' ppm');

                $('#temp-set-value').val(response.latest_temp.set_value);
                $('#ph-set-value').val(response.latest_ph.set_value);
                $('#do-set-value').val(response.latest_do.set_value);
                
            },
            error: function() {
                alert('An error occurred. Please try again.');
            }
        });
    });
});

// Alerts Scripts
$(document).ready(function() {
    function fetchLatestAlerts(sortOption) {
    $.ajax({
        type: 'GET',
        url: '/get_alerts',
        data: { sort: sortOption },
        success: function(response) {
            $('.alert-list').empty();
            response.forEach(function(alert) {
                var alertClass = alert.read ? '' : 'unread';
                var alertHtml = `
                    <li id="alert-${alert.id}" class="alert-item ${alertClass}">
                        <div class="alert-title">${alert.title}</div>
                        <div class="alert-description">${alert.description}</div>
                        <div class="alert-timestamp">${alert.timestamp}</div>
                        <div class="alert-actions">
                            ${alert.read ? '' : '<form class="set-read-form" data-alert-id="' + alert.id + '" method="POST" action="/set_alert_read/' + alert.id + '"><button type="submit" class="alert-mark-read-btn">Mark as Read</button></form>'}
                            <button class="alert-delete-btn" data-alert-id="${alert.id}">Delete</button>
                        </div>
                    </li>
                `;
                $('.alert-list').append(alertHtml);
            });

            $('.alert-delete-btn').click(function() {
                var alertId = $(this).data('alert-id');
                deleteAlert(alertId);
            });
        },
        error: function() {
            console.error('Error fetching alerts.');
        }
    });
    }

    function deleteAlert(alertId) {
        $.ajax({
            type: 'POST',
            url: '/delete_alert/' + alertId,
            success: function(response) {
                $('#alert-' + alertId).remove();
                console.log('Alert deleted successfully');
            },
            error: function() {
                console.error('Error deleting alert.');
            }
        });
    }

    fetchLatestAlerts('timestamp');
    $('.alert-sort-options input[type="radio"]').change(function() {
        var selectedSort = $(this).val();
        fetchLatestAlerts(selectedSort);
    });
    setInterval(function() {
        var selectedSort = $('.alert-sort-options input[type="radio"]:checked').val();
        fetchLatestAlerts(selectedSort);
    }, 10000);

    $(document).on('submit', '.set-read-form', function(event) {
        event.preventDefault();
        var form = $(this);
        var alertId = form.data('alert-id');
        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: form.serialize(),
            success: function(response) {
                if (response.success) {
                    $('#alert-' + alertId).removeClass('unread');
                    form.find('button').text('Read').attr('disabled', true);
                }
            },
            error: function() {
                alert('There was an error marking this alert as read.');
            }
        });
    });
});