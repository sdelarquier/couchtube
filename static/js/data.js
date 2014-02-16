// Find show and return result in modal
function getShow(show) {

  $.getJSON('shows', function(data) {

    var found = false;
    $.each(data, function(ind, val) {
      if (val['title']==show) {
        found = true;
        $('#modal-'+val['title_iso']).modal('show');
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
    console.log(data);
    $('#modal-search').find('.modal-body').html('');

    var out = "";
    if (data != 'None') {
      out += "<p>Is this the show you are looking for?</p>";
      out += "<p><b><span id='search-results'>"+data.Series.SeriesName+"</span>"
      out += " ("+data.Series.FirstAired.substr(0,4)+")"
      out += "</b></p>";
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
      $('#I-have-too-many-ids').html(
        '<div>Loading new show. This may take a while (1-2 minutes)</div>'
          +'<div class="progress progress-striped active">'
            +'<div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;">'
            +'</div>'
          +'</div>'
        +'</div>');

      sse = new EventSource("/ingestData?title="+show);
      sse.addEventListener('end', endStream, false);
      function endStream(event) {
        console.log('End stream', event.data);
        sse.close()
        data = event.data.split('\n');
        $('#I-have-too-many-ids').html(
          '<div>Your show is ready: '
          +data[3]+' out of '
          +data[2]
          +" episodes found ("+data[4]+" Free)."
          +'</div><a role="button" class="btn btn-primary" href="/watch?nm='
          +data[0]+'&yy='+data[1]+'">Start watching</a>');
      };
      sse.onmessage = function(message) {
        console.log(event.data);
        var pbar = $('#I-have-too-many-ids').find('.progress-bar');
        pbar.attr('aria-valuenow', message.data);
        pbar.attr('style', 'width: '+message.data+'%;');
      };
      // $.get("/ingestData?title="+show, function(data) {
      // });
    });

    $('#modal-search').modal('show');
  });
};
