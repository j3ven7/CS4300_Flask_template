var activeRow = "";

$(document).ready(function () {
    $("#show-results").height($("#map").outerHeight());
});

$(window).resize(function () {
    $("#show-results").height($("#map").outerHeight());
});

function toggle(element, lat, long) {

    // Revert the active row
    $("#detail" + activeRow).css("display", "none");
    $("#result" + activeRow).removeClass("active");
    $("#toggle" + activeRow).css("visibility", "hidden");

    // If the element is a new element
    var index = wypts.map(function (x) { return x.location.lat; }).indexOf(lat);
    if (activeRow != element) {
        if (activeRow != "") {
            while (index > -1) {
                wypts.splice(index, 1);
                index = wypts.map(function (x) { return x.location.lat; }).indexOf(lat);
            }
            updateMap(lat, long);
        }
        activeRow = element;
        $("#result" + activeRow).addClass("active");
        $("#detail" + activeRow).css("display", "block");
        $("#toggle" + activeRow).css("visibility", "visible");
        // document.getElementById("result" + activeRow).scrollIntoView();

        // No new active element - the element clicked is the currently active element
    } else {
        activeRow = "";
        while (index > -1) {
            wypts.splice(index, 1);
            index = wypts.map(function (x) { return x.location.lat; }).indexOf(lat);
        }
    }
}

function toggleMyRoute(element, lat, long, name) {

    // Plus sign active
    if ($("#toggle" + element).attr("src") == "static/images/plus.png") {
        $("#toggle" + element).attr("src", "static/images/minus.png")
        $("#toggle" + element).attr("src", "static/images/minus.png");
        slideDownNotification(name);
        // add waypoint
        wypts.push({ location: { lat: lat, lng: long }, stopover: true });
        wypt_names.push([name, element]);
    } else {
        $("#toggle" + element).attr("src", "static/images/plus.png")
        var i = wypt_names.indexOf(name);
        wypts.splice(i, 1);
        wypt_names.splice(i, 1);
        updateMap(lat, long);
    }
    populateMyRoute();
}

function populateMyRoute() {
    $("#myroute-container").height(function (index, height) {
        return (100 + 50 * wypt_names.length);
    });
    $("#myroute tbody").empty()
    for (w in wypt_names) {
        $("#myroute tbody").append(
            "<tr><td>" + wypt_names[w][0] + "<img src='static/images/minus.png' class='myroute-remove'\
        onclick='removeMyRoute(" + w + ")'></td></tr>");
    }
}

function removeMyRoute(i) {
    $("#toggle" + wypt_names[i][1]).attr("src", "static/images/plus.png")
    wypts.splice(i, 1);
    wypt_names.splice(i, 1);
    populateMyRoute();
}

function slideDownNotification(name = "") {

    if (name) {
        $("#confirmation").css("background-color", "#7fb800");
        $("#confirmation").text("Succesfully added " + name + " to your route!");

    } else {
        // empty string passed
        $("#confirmation").css("background-color", "#c32f27");
        $("#confirmation").text("Please enter a valid search query!");
    }
    $("#confirmation").css("opacity", "1");
    $("#confirmation").slideDown("fast").delay(2500).slideUp('fast');
}

function toggleQueryTab(i) {
    if (activeTab == i) {
        // Don't do anything since its already active
    } else {
        $("#query-tab" + activeTab).removeClass("active-tab")
        $("#result-table" + activeTab).removeClass("active-table")
        $("#query-tab" + i).addClass("active-tab")
        $("#result-table" + i).addClass("active-table")
        activeTab = i;
    }
}