var activeRow = "";

function toggle(element) {

    $("#detail" + activeRow).css("display", "none");
    $("#result" + activeRow).removeClass("active");
    if (activeRow != element) {
        activeRow = element;
        $("#result" + activeRow).addClass("active");
        $("#detail" + activeRow).css("display", "block");
        document.getElementById("result" + activeRow).scrollIntoView();

    } else {
        activeRow = "";
    }
}