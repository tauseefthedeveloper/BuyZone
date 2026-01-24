( function ( $ ) {
    $( document ).ready( function () {

        let zoomWidth;
        let zoomHeight;
        if($(window).width() >= 992){
            zoomWidth = 400;
            zoomHeight = 400
        }else{
            zoomWidth = 350,
            zoomHeight = 350
        }
        console.log(zoomHeight , zoomWidth)

        $( '.xzoom, .xzoom-gallery' ).xzoom( { zoomWidth: zoomWidth,zoomHeight:zoomHeight, tint: '#333', Xoffset: 15 , Yoffset:20} );
    } );
} )( jQuery );