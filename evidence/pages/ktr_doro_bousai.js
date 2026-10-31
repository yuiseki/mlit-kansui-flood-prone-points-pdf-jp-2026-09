var kiseiLayerGroup = new Array();

var kansuiLayerGroup = new Array();

map.fitBounds(L.latLngBounds(southWest, northEast));

function bousaiMapTile(pref) {

    var prefCode = pref.slice(3);
    this.utfgrid = new L.UtfGrid('../tiles/' + pref + '/{z}/{x}/{y}.json?callback=' + prefCode + '.lu_{z}_{x}_{y}', {

        resolution : 4,

        useJsonP : true,

        prefName : prefCode
    });

    this.tile = L.tileLayer('../tiles/' + pref + '/{z}/{x}/{y}.png', {

        maxZoom : 18,

        // unsupported by IE
        opacity : 0.7
    });

    this.utfgrid.on('click', function(e) {

        if (e.data) {
            var pdf = '../attachment/';

            var msg = e.data.no;
            if(msg === undefined){
                msg = e.data.NO;
            }

            var pdfName = e.data.pdf_name;
            if(pdfName === undefined){
                pdfName = e.data.PDF_NAME;
            }

            L.popup().setLatLng(e.latlng).setContent(msg + '<br>' + '<a href="' + pdf + pdfName + '" target="_blank">添付ファイル</a>').openOn(map);
        }
    });

    map.addLayer(this.utfgrid);

    map.addLayer(this.tile);

}

bousaiMapTile.prototype.removeTile = function() {

    map.removeLayer(this.utfgrid);

    map.removeLayer(this.tile);

    delete this.utfgrid;
    delete this.tile;
}

// 規制区間チェックボックス選択イベント
$(':input[id^=kisei]').click(function() {

    var pref = $(this).val();

    if ($(this).prop('checked')) {
        // add layer

        kiseiLayerGroup[pref] = new bousaiMapTile(pref);

    } else {
        // remove layer

        kiseiLayerGroup[pref].removeTile();

    }

});

// 冠水想定箇所チェックボックス選択イベント
$(':input[id^=kansui]').click(function() {

    var pref = $(this).val();

    if ($(this).prop('checked')) {
        // add layer

        var kml = new L.KML('../kml/' + pref + '.kml', {
            async : true
        });

        kansuiLayerGroup[pref] = kml;

        map.addLayer(kml);

    } else {
        // remove layer

        map.removeLayer(kansuiLayerGroup[pref]);

    }

});


