function findLoc(place, lt, lng) {
    return place.location.lat == lt && place.location.lng == lng;
}

var activeRow = "";

function toggle(element, lat, long) {

    // Revert the active row
    $("#detail" + activeRow).css("display", "none");
    $("#result" + activeRow).removeClass("active");
    $("#toggle" + activeRow).css("visibility", "hidden");


    // If the element is a new element
    var index = wypts.map(function (x) { return x.location.lat; }).indexOf(lat);
    if (activeRow != element) {
        if (activeRow != "") {
            if (index > -1) {
                wypts.splice(index, 1);
            }
        }
        activeRow = element;
        $("#result" + activeRow).addClass("active");
        $("#detail" + activeRow).css("display", "block");
        $("#toggle" + activeRow).css("visibility", "visible");
        // document.getElementById("result" + activeRow).scrollIntoView();

        // No new active element - the element clicked is the currently active element
    } else {
        activeRow = "";
        if (index > -1) {
            wypts.splice(index, 1);
        }
    }
}

function toggleMyRoute(element, lat, long) {

    // Plus sign active
    if ($("#toggle" + element).attr("src") == "static/images/plus.png") {
        $("#toggle" + element).attr("src", "static/images/minus.png")
        $("#toggle" + element).attr("src", "static/images/minus.png");
        $("#confirmation").css("opacity", "1");
        $("#confirmation").slideDown("fast").delay(2500).slideUp('fast');
        // add waypoint
    } else {
        $("#toggle" + element).attr("src", "static/images/plus.png")
        //wypts.push({ location: { lat: lat, lng: long }, stopover: true });
        var index = wypts.map(function (x) { return x.location.lat; }).indexOf(lat);
        console.log("TOGGLEMYROUTE: " + index);
        if (index > -1) {
            wypts.splice(index, 1);
        }

    }
}