
$(document).ready( function() {
	$(".file-upload-btn input[type=file]").css({ 
		"position": "fixed", 
		"right": "100%",
		"bottom": "100%"
	});

	$(".dpedit input[type=file]").each( function() { 
		$(this).change(function(ev) {
			$(".dpedit input[name$='-checked']").val("False")
			$(this).closest('form').submit()
		});
	});
});


$(window).on("load", function() {
	const ratio = 1.;
	$(".dpedit").each( function () {
		img = $(this).find("img")[0]
		console.log(img)
		var jcp = Jcrop.attach(img, {aspectRatio:ratio});
		xp1 = $(this).find("input[name$=xp1]").val();
		yp1 = $(this).find("input[name$=yp1]").val();
		xp2 = $(this).find("input[name$=xp2]").val();
		yp2 = $(this).find("input[name$=yp2]").val();
		w = img.width; h = img.height;
		w = img.naturalWidth; h = img.naturalHeight;
		x1 = w*xp1; x2 = w*xp2
		y1 = h*yp1; y2 = h*yp2
		w1 = x2-x1; h1 = y2-y1
		wh = Math.min(w1,h1)
		console.log(x1,y1,xp1,w)
		const rect = Jcrop.Rect.create(x1,y1,wh,wh);
		jcp.newWidget(rect);
		jcp.listen('crop.change',(widget,e) => {
			x1 = widget.pos.x; y1 = widget.pos.y
			x2 = x1 + widget.pos.w; y2 = y1 + widget.pos.h
			img = $($(widget.el).parents().eq(1)).children("img")[0];
			w = img.width; h = img.height;
			x1 = Math.max(x1/w,0.); Math.min(y1 = y1/h,1.)
			x2 = Math.max(x2/w,0.); Math.min(y2 = y2/h,2.)
			div = $(widget.el).parents().eq(2);
			$(div).children("input[name$=xp1]").val(x1);
			$(div).children("input[name$=yp1]").val(y1);
			$(div).children("input[name$=xp2]").val(x2);
			$(div).children("input[name$=yp2]").val(y2);
			$(div).children("input[name$=checked]").val('True')
		});
		jcp.focus();
	});
});
