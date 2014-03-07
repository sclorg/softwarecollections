$(function() {
    // we'll use a timer to load repo list whenever user stops typing
    // for 0.6 seconds (this number just feels right ;))
    var timer;

    $("#id_copr_username").on("keyup blur", function() {
        // coprnames_url has to be defined in template, since it's processed
        // on server-side
        if (timer) {
            clearTimeout(timer);
        }
        timer = setTimeout(function() {
            var url = coprnames_url.replace("__copr_username__",
                                            $("#id_copr_username").val());
            var $select = $("#id_copr_name");
            $select.empty();
            $.get(url, function(projects) {
                for (i in projects) {
                    $select.append(
                        $("<option>").attr("value", projects[i])
                            .text(projects[i])
                    );
                }
            }, "json");
        }, 600);
    });
});
