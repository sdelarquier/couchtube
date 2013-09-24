// episodes completeness
function modalOnShow() {

  if ($(this).find('svg').length==0) {
    var cont = d3.select(this).select(".container-bar");
    var show = d3.select(this).select(".info-bar").attr('data-name');
    var year = d3.select(this).select(".info-bar").attr('data-year');
    buildBar(show, year, cont);
  } else {
    modalOnResize();
  }

}

// episodes completeness
function modalOnResize() {

    var width = $(this).find(".container-bar").parent().width();
    var width_old = $(this).find("svg").attr("data-width");
    if (width > 0 & width_old > 0) {
      // console.log(width_old, width, width/width_old);
      $(this).find(".container-bar").width(width);
      d3.select(this).select('svg').attr('width', width);
      d3.select(this).select("g").attr("transform", "matrix(" + width/width_old + ",0,0,1,0,0)");
      // d3.select(this).select("rect").attr("transform", "matrix(" + width/width_old + ",0,0,0,0,0)");
    }

}

// Build chunked progress bar
function buildBar(show_name, show_year, parent) {

  var width = $(parent.node()).parent().width(),
      height = 20;

  var x = d3.scale.linear()
      .range([0, width])

  var y = d3.scale.ordinal()
      .rangeRoundBands([0, height], 0);

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("top");

  var svg = parent
      .attr("style", "width: "+(width+2)+"px")
    .append("svg")
      .attr("data-width", width)
      .attr("class", "progress")
      .attr("width", width)
      .attr("height", height)
    .append("g");

  d3.json("/completeness?nm="+show_name+'&yy='+show_year, function(error, data) {
    if (error) return console.warn(error);

    x.domain([0, data.episodes-1]);
    y.domain([0, 0]);

    svg.selectAll(".rect-bar")
        .data(data.found)
      .enter().append("rect")
        .attr("class", "rect-bar")
        .attr("x", function(d) { return x(d-1); })
        .attr("y", function(d) { return 0; })
        .attr("width", function(d) { return Math.abs(x(d) - x(d-1)); })
        .attr("height", y.rangeBand());

    svg.selectAll(".rect-bar-free")
        .data(data.free)
      .enter().append("rect")
        .attr("class", "rect-bar-free")
        .attr("x", function(d) { return x(d-1); })
        .attr("y", function(d) { return 0; })
        .attr("width", function(d) { return Math.abs(x(d) - x(d-1)); })
        .attr("height", y.rangeBand());

    parent.select(".info-bar")
      .html(data.found.length+'/'+data.episodes+' <font class="episode-free">('+data.free.length+' Free)</font>');
  });
}