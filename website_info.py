# This file has all the helper bits to make the website

# A piece of code that will cause the website to auto-refresh
def autorefresh_str(my_ip_addr):
    script_str = "<script>setInterval(function(){window.open('http://" + my_ip_addr + "', \"_self\")}, 3000);</script>"
    return script_str

# Function to return a piece of HTMl for the bar chart
def createBar(tick_count, day_of_week):
    # From the number of ticks, calculate the liters
    liters_used = tick_count * 0.06565217391
    
    # From the liters, calculate the percent of 600 L
    percent_used = int(liters_used / 600.0 * 100.0)
    
    if day_of_week == 0:
        day = "Monday"
    elif day_of_week == 1:
        day = "Tuesday"
    elif day_of_week == 2:
        day = "Wednesday"
    elif day_of_week == 3:
        day = "Thursday"
    elif day_of_week == 4:
        day = "Friday"
    elif day_of_week == 5:
        day = "Saturday"
    elif day_of_week == 6:
        day = "Sunday"
        
    # Create the HTML code snippet        
    if liters_used > 600:
        html_code = "<tr style=\"height:" + str(percent_used) + "%\"><th scope=\"row\">" + day + "</th><td><span><span class=\"blink_me\"><b><i>" + str(int(liters_used)) + " L</span></span></td>"
    else:                
        html_code = "<tr style=\"height:" + str(percent_used) + "%\"><th scope=\"row\">" + day + "</th><td><span>" + str(int(liters_used)) + " L</span></td>"
    return html_code


# HTML and CSS starting code
html_start = """<html>
<head>
<style>
/* Reference for blinking text */
/* https://stackoverflow.com/questions/16344354/how-to-make-blinking-flashing-text-with-css-3 */
.blink_me {
  animation: blinker 1s linear infinite;
}

@keyframes blinker {  
  50% { opacity: 0; }
}


/* Reference for bar chart */
/* https://codepen.io/inegoita/pen/YMrJGY */

body, table, input, select, textarea {
}

.graph {
	margin-bottom:1em;
    font:normal 100%/150% arial,helvetica,sans-serif;
}

.graph caption {
	font:bold 150%/120% arial,helvetica,sans-serif;
	padding-bottom:0.33em;
}

.graph tbody th {
	text-align:right;
}

@supports (display:grid) {

	@media (min-width:32em) {

		.graph {
			display:block;
            width:600px;
            height:300px;
		}

		.graph caption {
			display:block;
		}

		.graph thead {
			display:none;
		}

		.graph tbody {
			position:relative;
			display:grid;
			grid-template-columns:repeat(auto-fit, minmax(2em, 1fr));
			column-gap:2.5%;
			align-items:end;
			height:100%;
			margin:3em 0 1em 2.8em;
			padding:0 1em;
			border-bottom:2px solid rgba(0,0,0,0.5);
			background:repeating-linear-gradient(
				180deg,
				rgba(170,170,170,0.7) 0,
				rgba(170,170,170,0.7) 1px,
				transparent 1px,
				transparent 20%
			);
		}

		.graph tbody:before,
		.graph tbody:after {
			position:absolute;
			left:-3.2em;
			width:2.8em;
			text-align:right;
			font:bold 80%/120% arial,helvetica,sans-serif;
		}

		.graph tbody:before {
			content:"600 L"; /* Top of the graph, 100%, gets a label of 600 L */
			top:-0.6em;
		}

		.graph tbody:after {
			content:"0 L"; /* Bottom of the graph, 0%, gets a label of 0 L */
			bottom:-0.6em;
		}

		.graph tr {
			position:relative;
			display:block;
		}

		.graph tr:hover {
			z-index:999;
		}

		.graph th,
		.graph td {
			display:block;
			text-align:center;
		}

		.graph tbody th {
			position:absolute;
			top:-3em;
			left:0;
			width:100%;
			font-weight:normal;
			text-align:center;
            white-space:nowrap;
			text-indent:0;
			transform:rotate(-45deg);
		}

		.graph tbody th:after {
			content:"";
		}

		.graph td {
			width:100%;
			height:100%;
			background:rgba(104, 220, 238, 0.8); /* Colour of the vertical bars */
			border-radius:0.5em 0.5em 0 0;
			transition:background 0.5s;
		}

		.graph tr:hover td {
			opacity:0.7;
		}

		.graph td span {
			overflow:hidden;
			position:absolute;
			left:50%;
			top:50%;
			width:0;
			padding:0.5em 0;
			margin:-1em 0 0;
			font:normal 85%/120% arial,helvetica,sans-serif;
			font-weight:bold;
			opacity:0;
			transition:opacity 0.5s;
            color:white;
		}

		.toggleGraph:checked + table td span,
		.graph tr:hover td span {
			width:4em;
			margin-left:-2em; /* 1/2 the declared width */
			opacity:1;
		}

	} /* min-width:32em */

} /* grid only */

</style>

<title>Water Utilisation</title>
</head>

<body>
<br>
<br>
<br>
<table class="graph">
	<caption>Water usage over the week<br><br><br><br></caption>
	<thead>
		<tr>
			<th scope="col">Item</th>
			<th scope="col">Percent</th>
		</tr>
	</thead><tbody>
"""

# The HTML code for the end of the website
html_end = """	</tbody>
</table>

</body>

</html>"""

