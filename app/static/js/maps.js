var directionsRenderer;
var directionsService;
var coords = [];
var mapElement;
var map;
var origin;
var destination;
var initialDistance;
var initialTime;
var wypts = [];
var wypt_names = [];
var queries;
var dist;

function initMap() {
  var bounds = new google.maps.LatLngBounds();
  directionsRenderer = new google.maps.DirectionsRenderer;
  directionsService = new google.maps.DirectionsService;
  mapElement = document.getElementById('map');
  origin = coords[0];
  destination = coords[1];

  document.getElementById("origin-input").value = origin;
  document.getElementById("destination-input").value = destination;
  document.getElementById("distance-input").value = dist;
  for (var i = 0; i < queries.split(",").length; i++) {
    pushQueryHTML(queries.split(",")[i]);
  }

  map = new google.maps.Map(mapElement, {
    zoom: 7,
    center: {lat: 40.7128, lng: -74.0060} // Random start center, doesnt really matter
  });
  directionsRenderer.setMap(map);
  directionsService.route({
    origin: origin,
    destination: destination,
    travelMode: "DRIVING"
  }, function (response, status) {
    if (status == 'OK') {
      directionsRenderer.setDirections(response);
      var tt = 0;
      var td = 0;
      response["routes"][0]["legs"].forEach(function (leg, i) {
        tt += leg["duration"]["value"];
        td += leg["distance"]["value"];
      })
      initialTime = tt;
      initialDistance = td;
      var hrs = Math.floor(tt / 3600);
      var min = ((tt / 3600) - hrs) * 60;
      document.getElementById("time").innerHTML = "Total time: " + hrs + " hours " + Math.floor(min) + " minutes"
      document.getElementById("distance").innerHTML = "Total distance: " + (td / 1609.34).toFixed(1) + " miles"

    } else if (status == 'ZERO_RESULTS') {
      // catch error
      console.log("There are no results for this route.")
    } else {
      window.alert('Directions request failed due to ' + status);
    }
  });
}

function updateMap(lat = null, long = null) {
  //console.log(wypts);
  if (lat == null && long == null) {
    // Reset button clicked
    wypts = [];
    $("#result" + activeRow).removeClass("active");
    $("#detail" + activeRow).css("display", "none");
    activeRow = "";
  } else {
    var temp_wypts = [];
    // opening place for the first time
    if (!($("#result" + activeRow).hasClass("active"))) {
      for (var i = 0; i < wypts.length; i++) {
        temp_wypts.push(wypts[i]);
      }
      var index = wypts.map(function (x) { return x.location.lat; }).indexOf(lat);
      // only add to temp if not already in route
      if (index == -1) {
        temp_wypts.push({
          location: {
            lat: lat,
            lng: long
          },
          stopover: true
        });
      }
    }
  }
  var mapElement = document.getElementById('map');
  directionsService.route({
    origin: origin,
    destination: destination,
    waypoints: ($("#result" + activeRow).hasClass("active")) ? wypts : temp_wypts,
    optimizeWaypoints: true,
    travelMode: "DRIVING"
  }, function (response, status) {
    if (status == 'OK') {
      var tt = 0;
      var td = 0;
      response["routes"][0]["legs"].forEach(function (leg, i) {
        tt += leg["duration"]["value"];
        td += leg["distance"]["value"];
      })
      var changeTime = tt - initialTime;
      var changeHrs = Math.floor(changeTime / 3600);
      var changeMin = Math.floor(((changeTime / 3600) - changeHrs) * 60);

      var changeDist = td - initialDistance;

      var hrs = Math.floor(tt / 3600);
      var min = ((tt / 3600) - hrs) * 60;

      if (lat == null && long == null) {
        document.getElementById("time").innerHTML = "Total time: " + hrs + " hours " + Math.floor(min) + " minutes"
        document.getElementById("distance").innerHTML = "Total distance: " + (td / 1609.34).toFixed(1) + " miles"
      }
      else {
        document.getElementById("time").innerHTML = "Total time: " + hrs + " hours " + Math.floor(min) + " minutes ( " + changeHrs + " hour " + changeMin + " minute detour )"
        document.getElementById("distance").innerHTML = "Total distance: " + (td / 1609.34).toFixed(1) + " miles ( " + (changeDist / 1609.34).toFixed(1) + " mile detour )"
      }

      directionsRenderer.setDirections(response);
    } else {
      window.alert('Directions request failed due to ' + status);
    }
  });
}