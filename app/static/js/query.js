var queryList = [];

function pushQueryHTML(input) {
    queryList.push(input);
    var query_box = $("<div class='single-query'>" + input + "<img src='/static/images/x.png'></div>");
    
    query_box.mouseenter(function() {
        query_box.find("img").addClass("spun");
        setTimeout(function(){
            query_box.find("img").removeClass("spun");
        }, 400);
    });
    
    query_box.click(function() {
        query_box.hide("340");
        queryList.splice(queryList.indexOf(input), 1);
    });

    $(".queries-container").css("max-height", "1000px");
    $(".queries-container").append(query_box);
}

function addToQuery(e) {
    var keyCode = e.keyCode || e.which;
    if (keyCode === 13 || e.type == "click") { 
        e.preventDefault();
        var input = $("#description-input").val();
        $("#description-input").val("");
        if (!input) {
            slideDownNotification();
        } else {
            if (queryList.indexOf(input) == -1) {
                pushQueryHTML(input);
            }
        }
    }
    return false;
}

function submitQuery(e) {
    if (queryList.length == 0) {
        slideDownNotification();
        e.preventDefault();
        return false;
    }
    $("input[name='description']").val(queryList.toString());
    if ($("#distanceInput").val() == "101") {
        $("input[name='distance']").val("3000");
    } else {
        $("input[name='distance']").val($("#distanceInput").val());
    }
}