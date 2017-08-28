
jQuery(function () {
    jQuery('[data-tooltip="toggle"]').tooltip({container: '.container'});
    jQuery('.tabs h6').click(function(){
        jQuery('.tabs h6').removeClass('active');
        jQuery('.tabs-content .tab').removeClass('active');
        var tab = jQuery(this).data('tab');
        jQuery('.tabs h6.' + tab).addClass('active');
        jQuery('.tabs-content .tab.' + tab).addClass('active');
    });
    jQuery('.media .media-actions .icon.watch').click(function(){
        var media = jQuery(this).closest('.media');
        var type = media.data('media-type');
        jQuery(this).prop('disabled', true);
        jQuery.ajax({url: '/' + type + '/watch/' + media.data('tmdbid'), context: this,
        success: function(result){
            if (result.result)
            {
                jQuery(this).removeClass('active');
                media.find('.media-actions .icon.' + jQuery(this).data('swap')).addClass('active');
            }
            else
            {
                alert('Unable to update ' + type + ' watch status: ' + result.data);
            }
            jQuery(this).prop('disabled', false);
        }});
    });
    jQuery('.media .media-actions .icon.unwatch').click(function(){
        var media = jQuery(this).closest('.media');
        var type = media.data('media-type');
        jQuery(this).prop('disabled', true);
        jQuery.ajax({url: '/' + type + '/unwatch/' + media.data('tmdbid'), context: this,
        success: function(result){
            if (result.result)
            {
                jQuery(this).removeClass('active');
                media.find('.media-actions .icon.' + jQuery(this).data('swap')).addClass('active');
            }
            else
            {
                alert('Unable to update ' + type + ' watch status: ' + result.data);
            }
            jQuery(this).prop('disabled', false);
        }});
    });
    function swapTitle(element)
    {
        var el = jQuery(element);
        el.addClass('spin').addClass('active');
        var tool = el.attr('title');
        el.attr('title', el.data('alt-title'));
        el.data('alt-title', tool);
        el.tooltip('fixTitle');
    }
    jQuery('.media.view .media-actions .icon.refresh').click(function(){
        if (jQuery(this).hasClass('spin'))
            return;
        var type = jQuery('.media.view').data('media-type');
        jQuery.ajax({url: '/' + type + '/refresh/' + jQuery('.media.view').data('tmdbid'), context: this,
        success: function(result){
            if (result.result)
            {
                jQuery(this).addClass('spin').addClass('notify');
                swapTitle(jQuery(this));
                var checkTimer = setTimeout(checkFunction, 1000);
                function checkFunction()
                {
                    jQuery.ajax({url: '/' + type + '/refresh_status/' + jQuery('.media.view').data('tmdbid'), context: this,
                    success: function(result){
                        if (result.result)
                        {
                            checkTimer = setTimeout(checkFunction, 1000);
                        }
                        else
                        {
                            jQuery(this).removeClass('spin').removeClass('notify');
                            swapTitle(jQuery(this));
                            clearTimeout(checkTimer);
                        }
                    }, error: function(result){
                            checkTimer = setTimeout(checkFunction, 1000);
                    }});
                }
            }
            else
            {
                alert('Unable to refresh ' + type + ' library item: ' + result.data);
            }
        }, error: function(result){
                alert('Unable to refresh ' + type + ' library item: ' + result.data);
        }});
    });
    jQuery('.media.view .media-actions .icon.add').click(function(){
        var type = jQuery('.media.view').data('media-type');
        var refresh = jQuery('.media.view .media-actions .icon.refresh');
        refresh.addClass('spin').addClass('active').attr('title', 'Adding to local library').tooltip('fixTitle');
        jQuery(this).removeClass('active');
        jQuery.ajax({url: '/' + type + '/add/' + jQuery('.media.view').data('tmdbid'), context: this,
        success: function(result){
            if (result.result)
            {
                refresh.removeClass('spin');
                location.reload(true);
            }
            else
            {
                alert('Unable to add ' + type + ' item to library: ' + result.data);
            }
        }, error: function(result){
                alert('Unable to add ' + type + ' item to library: ' + result.data);
        }});
    });
    jQuery('.media.view .media-actions .icon.settings').click(function(event){
        var div = jQuery('.media.view .media-settings .slider');
        if (div.hasClass('opened'))
            div.removeClass('opened');
        else
            div.addClass('opened');
        event.stopPropagation();
    });
    jQuery(window).click(function() {
        var div = jQuery('.media.view .media-settings .slider');
        if (div.hasClass('opened'))
            div.removeClass('opened');
    });
    jQuery('.media.view .media-settings .slider').click(function(event){
        event.stopPropagation();
    });
    jQuery('.media.view .media-settings .slider .actions .btn.cancel').click(function(event){
        jQuery('.media.view .media-settings .slider').removeClass('opened');
    });
    jQuery('#confirm-delete .btn-ok').click(function(e) {
        var type = jQuery('.media.view').data('media-type');
        var modalDiv = jQuery(e.delegateTarget);
        modalDiv.addClass('loading');
        jQuery.ajax({url: '/' + type + '/remove/' + jQuery('.media.view').data('tmdbid'), context: this,
        success: function(result){
            if (result.result)
            {
                modalDiv.modal('hide').removeClass('loading');
                location.reload(true);
            }
            else
            {
                alert('Unable to remove ' + type + ' item from library: ' + result.data);
            }
        }, error: function(result){
                alert('Unable to remove ' + type + ' item from library: ' + result.data);
        }});
    });
    jQuery('.sort-actions button.sort.list').click(function() {
        jQuery('.sort-actions button.sort.grid').show();
        jQuery(this).hide();
        jQuery('.media-list').show();
        jQuery('.media-grid').hide();
        Cookies.set('mm_' + jQuery('.sort-actions').data('media-type') + '_sort', 'list');
    });
    jQuery('.sort-actions button.sort.grid').click(function() {
        jQuery('.sort-actions button.sort.list').show();
        jQuery(this).hide();
        jQuery('.media-grid').show();
        jQuery('.media-list').hide();
        Cookies.set('mm_' + jQuery('.sort-actions').data('media-type') + '_sort', 'grid');
    });
    jQuery('.log-list .log-item').click(function() {
        var div = jQuery(this).next('.log-data');
        if (div.hasClass('open'))
        {
            div.removeClass('open');
            div.addClass('closed');
        }
        else
        {
            div.removeClass('closed');
            div.addClass('open');
        }
    });
    jQuery('.overview-actions .icon.refresh').click(function(){
        if (jQuery(this).hasClass('spin'))
            return;
        jQuery.ajax({url: '/refresh', context: this,
        success: function(result){
            if (result.result)
            {
                jQuery(this).addClass('spin').addClass('notify');
                swapTitle(jQuery(this));
                var checkTimer = setTimeout(checkFunction, 1000);
                function checkFunction()
                {
                    jQuery.ajax({url: '/refresh/status', context: this,
                    success: function(result){
                        if (result.result)
                        {
                            checkTimer = setTimeout(checkFunction, 1000);
                        }
                        else
                        {
                            jQuery(this).removeClass('spin').removeClass('notify');
                            swapTitle(jQuery(this));
                            clearTimeout(checkTimer);
                        }
                    }, error: function(result){
                            checkTimer = setTimeout(checkFunction, 1000);
                    }});
                }
            }
            else
            {
                alert('Unable to refresh library');
            }
        }, error: function(result){
                alert('Unable to refresh library');
        }});
    });
});
