// Find show and return result in modal
function getShow(show) {

  $.getJSON('shows', function(data) {

    var found = false;
    $.each(data, function(ind, val) {
      // console.log(ind, val);
      if (val['title']==show) {
        found = true;
        $('#modal-'+show.replace(/ /g, "")).modal('show');
      }
    });

    if (found == false) {
      $('#modal-alert').find('.modal-body').find('#alert-show-title').html(show);
      $('#modal-alert').modal('show');
    }
  });
};

// Add show to app
function addShow() {
  $('#modal-alert').modal('hide');
  var show = $('#show-typeahead').val();
  $('#modal-search').find('.modal-body').html('<img src="static/img/ajax-loader.gif">')

  $.get("/findShow?title="+show, function(data) {

    $('#modal-search').find('.modal-body').html('');

    var out = "";
    if (data != 'None') {
      out += "<p>Is this the show you are looking for?</p>";
      out += "<p><b><span id='search-results'>"+data.Series.SeriesName+"</span> ("+data.Series.FirstAired.substr(0,4)+")</b></p>";
      if (data.Series.banner) {
        out += "<img class='img-thumbnail' src='http://thetvdb.com/banners/"+data.Series.banner+"'>";
      }
      out += '<p></p>';
      out += '<div id="I-have-too-many-ids"><button type="button" class="btn btn-primary" id="yt-get-show">Yes, get it!</button></div>';
    } else {
      out += "<p>Sorry, I could not find your show...</p>";
    }
    $('#modal-search').find('.modal-body').html(out);

    // Start show loader engine
    $('#yt-get-show').click(function() {
      var show = $('#modal-search').find('#search-results').text();
      console.log('Get show ', show)
      $('#I-have-too-many-ids').html('<div>This may take a while (1-2 minutes)</div><img src="static/img/ajax-loader.gif">');
      $.get("/ingestData?title="+show, function(data) {
        $('#I-have-too-many-ids').html('<div>Your show is ready: '+data.ytcount+' out of '+data.episodes+' episodes found.</div><a role="button" class="btn btn-primary" href="/watch?nm='+data.title+'&yy='+data.year+'">Start watching</a>');
      });
    });

    $('#modal-search').modal('show');
  });
};


