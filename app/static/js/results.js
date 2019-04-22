var activeRow = "";

function toggle(element) {

    // Revert the active row
    $("#detail" + activeRow).css("display", "none");
    $("#result" + activeRow).removeClass("active");
    $("#toggle" + activeRow).css("visibility", "hidden");

    // If the element is a new element
    if (activeRow != element) {
        activeRow = element;
        $("#result" + activeRow).addClass("active");
        $("#detail" + activeRow).css("display", "block");
        $("#toggle" + activeRow).css("visibility", "visible");
        // document.getElementById("result" + activeRow).scrollIntoView();

    // No new active element
    } else {
        activeRow = "";
    }
}

function toggleMyRoute(element) {

    // Plus sign active
    if ($("#toggle" + element).attr("src") == "static/images/plus.png") {
        $("#toggle" + element).attr("src", "static/images/minus.png");
        $("#confirmation").css("opacity", "1");
        $("#confirmation").slideDown("fast").delay(2500).slideUp('fast');
        // add waypoint
    } else {
        $("#toggle" + element).attr("src", "static/images/plus.png");
    }
}