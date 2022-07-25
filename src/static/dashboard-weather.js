// Coded By Ramesh Syangtan @ramesh_syn on twitter
$(document).ready(function() {
  var apiId = "5264779432aa5523b400895723caa06e"; // weather api key : openweathermap.org
  // Getting user Ip and location information from http://ipinfo.io JSON API
  $.getJSON("https://ipinfo.io/", function(location) {
    var latLon = location.loc.split(","); // Longitute and Latitude
    var lat = latLon[0];
    var lon = latLon[1];
    var cityName = location.city;
    var country = location.country;
    // Openweathermap.com API URL
    var apiUrl = "https://api.openweathermap.org/data/2.5/weather?lat=" + lat + "&lon=" + lon + "&appid=" + apiId;

    // Getting weather information from openweathermap.org API
    $.getJSON(apiUrl, function(w) {
      var wId = w.weather[0].id;
      var wType = w.weather[0].main; // Type of weather
      var temp = w.main.temp; // Temperature in Kelvin unit
      var wIconId = w.weather[0].icon;
      var celsius = temp - 273.15;
      var isCelsius = true;
      var windSpeed = w.wind.speed; // wind speed
      var wIconUrl = "http://openweathermap.org/img/w/" + wIconId + ".png";
      var imageLink = {
        thunderStorm: "url(http://extrawall.net/images/wallpapers/529_1920x1080_thunderstorm_over_grand_canyon.jpg)",
        drizzle: "url(https://www.gloucestercitizen.co.uk/images/localworld/ugc-images/276271/Article/images/21342065/6290248-large.jpg)",
        rain: "url(http://runlifthavefun.com/wp-content/uploads/2014/11/A-Rainy-Day.jpg)",
        snow: "url(https://iskin.co.uk/wallpapers/styles/1920x1080/public/snow_drifts.jpg)",
        clear: "url(http://xdesktopwallpapers.com/wp-content/uploads/2011/05/Clear-Sky-in-a-sunny-day.jpg)",
        cloud: "url(http://alliswall.com/file/1718/1920x1200/16:9/cloudy-weather-2.jpg)",
        mist: "url(http://static5.businessinsider.com/image/5390bbeb6bb3f7407d6ba579/why-different-weather-apps-give-you-different-forecasts.jpg)",
      }
      var weatherImage = "";

      function selectWImage(weatherId) {
        if (weatherId >= 200 && weatherId < 300) weatherImage = imageLink.thunderStorm;
        else if (weatherId >= 300 && weatherId < 400) weatherImage = imageLink.drizzle;
        else if (weatherId >= 500 && weatherId < 600) weatherImage = imageLink.rain;
        else if (weatherId >= 600 && weatherId < 800) weatherImage = imageLink.snow;
        else if (weatherId === 800) weatherImage = imageLink.clear;
        else if (weatherId > 800 && weatherId < 900) weatherImage = imageLink.cloud;
        else weatherImage = imageLink.mist;
      }
      selectWImage(wId);
      var cssProp = "background";
      var cssValue = weatherImage + "no-repeat fixed";
      $("html").css(cssProp, cssValue);
      $("html").css("background-size", "cover");
      $(".weather-info img").attr("src", wIconUrl);      
      $("#temp span").html(celsius.toFixed(1)  + " &#8451");
      $("#weather-type").html(wType);
      $("#wind-speed").html(windSpeed + " m/s");
      $("#location").html(cityName + ", " + country);
      $(".weather").addClass('animated zoomIn');

      function sCelsius() {
        $("#temp span").html(celsius.toFixed(1) + " &#8451");
        isCelsius = true;
      }

      function sFarenheit() {
        var f = celsius * 9 / 5 + 32;
        $("#temp span").html(Math.floor(f) + " &#8457");
        isCelsius = false;
      }
      $("#temp span").click(function() {
        (isCelsius) ? sFarenheit(): sCelsius();
      });

    });

  });

});