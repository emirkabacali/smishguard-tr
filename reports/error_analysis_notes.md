## Observations (written by hand after the single test run)

**Overall.** The hybrid system made 6 errors on 112 test messages; the ML-only system made 5.
The only difference is one telecom bill notice (ML probability 0.55, just below the ML-only
threshold) that the `MONEY_OR_FINE` rule (+0.10) pushed over the hybrid threshold. With 112
messages this one-message gap is well inside the bootstrap confidence intervals, so the data
does not show that either system is better. On this 2010–2011 data the rules add explanations
but no measurable accuracy over the text model.

**False positives**

1. *Bank password notice asking the user to click and enter card details.* Labeled legitimate
   in TurkishSMS, but the text is what a phishing message looks like today. Neither a model nor
   a human could separate it from phishing by its text alone; only checking the domain
   (`finansbank.com.tr`, not in our brand allowlist) would help.
2. *Membership password notification.* `CREDENTIAL_REQUEST` fires on "şifreniz" although the
   message *sends* a password instead of *asking* for one. A known limitation of keyword rules.
3. *Real cargo notice about an unreachable address.* This is exactly the template that cargo
   smishing imitates. `ADDRESS_ISSUE` did not fire because "teslim edilemem**iş**tir" is not
   covered by the pattern `teslim edilemed`. The pattern was **not** changed after seeing the
   test set (that would leak test information); it is listed as future work.
4. *Telecom bill reminder with an amount in TL.* Borderline ML score; see "Overall".

**False negatives**

Both missed messages are labeled spam but contain no call to action: a national-holiday
greeting from a company and a "your package price did not change" notice from an ISP.
TurkishSMS labels unsolicited commercial messages as spam even when they are harmless, so
these are disagreements about the *definition* of malicious rather than missed scams.

**Takeaways**

- Recall on real malicious messages is high (49/51) for both ML and hybrid; most errors come
  from legitimate institutional messages that resemble scams.
- The rule engine is precise on modern smishing (see the curated table) but low-recall on the
  old advertising spam that dominates the test set.
- Better evaluation needs more *recent, real* labeled messages (`curated_real`), which is the
  main roadmap item.
