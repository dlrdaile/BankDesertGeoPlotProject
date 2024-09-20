window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const {
                colorscale,
                style,
                counties,
                is_highly
            } = context.hideout; // get props from hideout
            style.fillColor = colorscale[2];
            if (is_highly) {
                if (counties && counties.includes(feature.properties.COUNTY_NAME)) {
                    // style.fillColor = colorscale[6];
                    style.fillOpacity = 0.8;
                    style.color = 'black';
                    // style.dashArray = '1';
                    // style.weight = 1;
                } else {
                    style.fillOpacity = 0.2;
                    style.color = 'white';
                    // style.dashArray = '1';
                    // style.weight = 0.1;
                }
            }
            return style;
        },
        function1: function(feature, layer, context) {
            layer.bindTooltip(`<div class="content">
    <div><strong>FIPSWITHTRACT:</strong>${feature.id}</div>
    <div><strong>STATE:</strong>${feature.properties.STATE_NAME}</div>
    <div><strong>is_highly:</strong>${feature.properties.is_highly}</div>
    <div><strong>TRACT:</strong>${feature.properties.TRACTCE10}</div>
    <div><strong>COUNTY:</strong>${feature.properties.COUNTY_NAME}</div>
</div>`)
        },
        function2: function(feature, layer, context) {
            // if it is a cluster, don't bind popup
            // layer.bindTooltip(`<div class="marker-content">
            if (feature.properties.TRACTCE10) {
                layer.bindPopup(`<div class="marker-content">
        <div><strong>Tract:</strong>${feature.properties.TRACTCE10}</div>
        <div><strong>State:</strong>${feature.properties.STATE_NAME}</div>
        <div><strong>Country:</strong>${feature.properties.COUNTY_NAME}</div>
        <div><strong>Name:</strong>${feature.properties.namefull}</div>
        <div><strong>Addresbr:</strong>${feature.properties.addresbr}</div>
</div>`);
            }
        },
        function3: function(feature, latlng, context) {
            const scatterIcon = L.DivIcon.extend({
                createIcon: function(oldIcon) {
                    let icon = L.DivIcon.prototype.createIcon.call(this, oldIcon);
                    icon.style.backgroundColor = this.options.color;
                    return icon;
                }
            })
            const icon = new scatterIcon({
                className: "marker-cluster",
                iconSize: L.point(20, 20),
                color: 'red',
            });
            const marker = L.marker(latlng, {
                icon: icon
            }); // render a simple circle marker
            return marker; // render a simple circle marker
        }
    }
});