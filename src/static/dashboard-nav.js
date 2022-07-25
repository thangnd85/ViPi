// ---------vertical-menu with-inner-menu-active-animation-----------
	
		$(document).ready(function(){
			var urlCurrent = window.location.pathname;
			urlCurrent = urlCurrent.replace('/', '');
			if(!urlCurrent){
				urlCurrent = 'home';
			}
			$('.main-navbar li, .navbar-nav li').removeClass('active');
			$('.main-navbar, .navbar-nav').find('.'+urlCurrent).addClass('active');
			var widthDevice = $( window ).width();
			var className = '#accordian';
			if(widthDevice < 900){
				 className = '#nav-mobile';
			}
			var tabsVerticalInner = $(className);
		var selectorVerticalInner = $(className).find('li').length;
		var activeItemVerticalInner = tabsVerticalInner.find('.active');
		var activeWidthVerticalHeight = activeItemVerticalInner.innerHeight();
		var activeWidthVerticalWidth = activeItemVerticalInner.innerWidth();
		var itemPosVerticalTop = activeItemVerticalInner.position();
		var itemPosVerticalLeft = activeItemVerticalInner.position();
		$(".selector-active").css({
		  "top":itemPosVerticalTop.top + "px", 
		  "left":itemPosVerticalLeft.left + "px",
		  "height": activeWidthVerticalHeight + "px",
		  "width": activeWidthVerticalWidth + "px"
		});
			console.log(urlCurrent);
		})