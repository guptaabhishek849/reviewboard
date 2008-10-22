<?php

$THERMOMETER_GOAL = 2000;
$THERMOMETER_CURRENT = 0;

$THERMOMETER_ITEMS = array(
	2000 => "Web hosting (1 year)",
	1000  => "Web hosting (6 months)",
);

function display_thermometer()
{
	global $THERMOMETER_ITEMS, $THERMOMETER_GOAL, $THERMOMETER_CURRENT;

	$cur_pct = $THERMOMETER_CURRENT / $THERMOMETER_GOAL * 100;
	$empty_pct = 100 - $cur_pct;
?>
<div id="thermometer">
 <div class="meter">
<?php
	foreach ($THERMOMETER_ITEMS as $amount => $description) {
		$top = 100 - $amount / $THERMOMETER_GOAL * 100;
		print "  <div class=\"item\" style=\"top:$top%;\">$description<br />$$amount.00</div>\n";
	}
?>
  <div class="empty" style="height:<?php print $empty_pct; ?>%;">&nbsp;</div>
  <div class="full" style="height:<?php print $cur_pct; ?>%;">&nbsp;</div>
 </div>
 <img src="/images/thermometer_bottom.png" width="52" height="48" alt="" />
</div>

<?php
}

?>