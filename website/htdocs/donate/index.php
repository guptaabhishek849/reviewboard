<?php
    require "html.inc.php";
    require "thermometer.inc.php";

    site_start("Donating");

	display_thermometer();
?>
<h1>Donating to Review Board</h1>
<p>
 The developers of the Review Board project are committed to providing
 free, high-quality software to aid in the code review process. This
 in turn saves you time and money in the development of your own software.
</p>
<p>
 If you've found Review Board to be useful, please consider making a
 donation to help us with our development and maintenance costs. We use
 <a href="http://www.paypal.com/">PayPal</a>, which accepts credit and debit
 cards.
</p>
<p>
 Your donation will help us to cover our growing web hosting costs and
 will go toward sub-projects that we hope to pursue in the future.
</p>

<h2>Make a one-time donation</h2>
<p>
 Donate using your credit card or PayPal account. If you're not sure how
 much to donate, we recommend $10, $20 or $50, but will gladly accept
 donations of any size.
</p>

<form action="https://www.paypal.com/cgi-bin/webscr" method="post">
 <input type="hidden" name="cmd" value="_donations" />
 <input type="hidden" name="business" value="donate@review-board.org" />
 <input type="hidden" name="item_name" value="Review Board" />
 <input type="hidden" name="item_number" value="10001" />
 <input type="hidden" name="page_style" value="PayPal" />
 <input type="hidden" name="no_shipping" value="1" />
 <input type="hidden" name="cn" value="Additional Feedback" />
 <input type="hidden" name="currency_code" value="USD" />
 <input type="hidden" name="tax" value="0" />
 <input type="hidden" name="lc" value="US" />
 <input type="hidden" name="bn" value="PP-DonationsBF" />
 <input type="image" src="https://www.paypal.com/en_US/i/btn/btn_donate_LG.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!" />
 <img alt="" border="0" src="https://www.paypal.com/en_US/i/scr/pixel.gif" width="1" height="1" />
</form>

<h2>Make a recurring donation</h2>
<p>
 If you want to help us with our fees on a monthly basis, you can automatically
 donate every month.
</p>
<form action="https://www.paypal.com/cgi-bin/webscr" method="post">
 <input type="hidden" name="cmd" value="_xclick-subscriptions" />
 <input type="hidden" name="business" value="donate@review-board.org" />
 <input type="hidden" name="no_shipping" value="1" />
 <input type="hidden" name="item_name" value="Monthly donation to the Review Board project" />
 <input type="hidden" name="cbt" value="Continue" />
 <input type="hidden" name="bn" value="PP-SubscriptionsBF" />
 <input type="hidden" name="currency_code" value="USD" />
 <input type="hidden" name="p3" value="1" />
 <input type="hidden" name="t3" value="M" />
 <input type="hidden" name="src" value="1" />
 <input type="hidden" name="sra" value="1" />
 <img alt="" border="0" src="https://www.paypal.com/en_US/i/scr/pixel.gif" width="1" height="1" />

 <p>
  <input type="image" src="https://www.paypal.com/en_US/i/btn/btn_donate_LG.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!" style="vertical-align: bottom;" />
  Amount:
  <select name="a3">
   <option value="5.00">$5</option>
   <option value="10.00">$10</option>
   <option value="15.00" selected="selected">$15</option>
   <option value="20.00">$20</option>
   <option value="25.00">$25</option>
   <option value="30.00">$30</option>
   <option value="50.00">$50</option>
   <option value="100.00">$100</option>
   <option value="200.00">$200</option>
   <option value="500.00">$500</option>
  </select>
 </p>
</form>

<p>
 To cancel a monthly donation,
 <a href="https://www.paypal.com/us/cgi-bin/webscr?cmd=_login-run">log in</a>
 to your PayPal account and go to the <b>Profile</b> tab. In the
 Financial Information column, click <b>Recurring Payments</b>. Find
 "Review Board" and click <b>View Payment</b>, and then <b>Cancel</b>.
</p>

<?php
	site_end();
?>