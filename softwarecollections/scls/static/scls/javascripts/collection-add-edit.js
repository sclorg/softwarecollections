$(function() {
    // we'll use a timer to load repo list whenever user stops typing
    // for 0.6 seconds (this number just feels right ;))
    var timer;
    // remember last synced copr username, so that we don't refresh
    // unnecessarily, e.g. after a blur that follows keyup
    var last_synced_username;
    var last_sync_successful;

    $("#id_copr_username").on("keyup blur", function() {
        // coprnames_url has to be defined in template, since it's processed
        // on server-side
        if (timer) {
            clearTimeout(timer);
        }
        timer = setTimeout(function() {
            var curr_name = $("#id_copr_username").val()
            if (last_sync_successful && last_synced_username == curr_name) {
                return
            } else {
                last_sync_successful = false
            }
            var url = coprnames_url.replace("__copr_username__", curr_name);
            var $select = $("#id_copr_name");
            $select.empty();
            $.get(url, function(projects) {
                for (i in projects) {
                    $select.append(
                        $("<option>").attr("value", projects[i])
                            .text(projects[i])
                    );
                }
                // only set last_sync* if we were successful
                last_synced_username = curr_name
                last_sync_successful = true
            }, "json");
        }, 600);
    });
});
