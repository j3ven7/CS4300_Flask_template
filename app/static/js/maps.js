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
var activeTab = 0;

function initMap() {
	var bounds = new google.maps.LatLngBounds();
	directionsRenderer = new google.maps.DirectionsRenderer;
	directionsService = new google.maps.DirectionsService;
	mapElement = document.getElementById('map');
	origin = coords[0];
	destination = coords[1];

	document.getElementById("origin-input").value = origin;
	document.getElementById("destination-input").value = destination;
	document.getElementById("distanceInput").value = (dist == 3000) ? 3000 : dist;
	document.getElementById("distanceText").value = (dist == 3000) ? "100+ miles" : (dist == 1) ? "1 mile" : dist + " miles";

	queries = queries.split(",");
	for (var i = 0; i < queries.length; i++) {
		pushQueryHTML(queries[i]);
		addTab(i);
	}
	$("#query-tab0").addClass("active-tab");
	$("#result-table0").addClass("active-table");

	map = new google.maps.Map(mapElement, {
		zoom: 7,
		center: { lat: 40.7128, lng: -74.0060 } // Random start center, doesnt really matter
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
			});
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

function updateMap(lat = null, long = null, refresh=false) {
	//console.log(wypts);
	if (lat == null && long == null && !refresh) {
		// Reset button clicked
		wypts = [];
		wypt_names = [];
    populateMyRoute();
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
			if (index == -1 && !refresh) {
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
				document.getElementById("time").innerHTML = "Total time: " + hrs + " hours " + Math.floor(min) + " minutes <span>( + " + changeHrs + " hour " + changeMin + " minute detour )</span>";
				document.getElementById("distance").innerHTML = "Total distance: " + (td / 1609.34).toFixed(1) + " miles <span>( + " + (changeDist / 1609.34).toFixed(1) + " mile detour )</span>"
			}
			directionsRenderer.setDirections(response);
		} else {
			window.alert('Directions request failed due to ' + status);
		}
	});
}

function addTab(query_i) {
	var new_tab = "<div class='tab' id='query-tab" + query_i + "' onclick='toggleQueryTab(" + query_i + ")'><p>" + queries[query_i] + "</p></div>";
	document.getElementById("results-tabs").innerHTML += new_tab;
}

function catchBadWaypoints() {
	$("#confirmation").css("background-color", "#c32f27");
	$("#confirmation").text("Please enter a valid origin and destination!");
	$("#confirmation").css("opacity", "1");
	$("#confirmation").slideDown("fast").delay(5000).slideUp('fast');
}