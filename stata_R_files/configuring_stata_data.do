** took ACS_processed_2011 from skills_USA and giving to Daniel

use "/Users/vs3041/Dropbox (Princeton)/Irreducible Error/LTP_final/usa_00014.dta", clear

keep educ empstat age sex fertyr marst uhrswork incwage metro gq nfams sei vetstat trantime 

* Winsorize variable at the 1st and 99th percentiles
gen income_clean = incwage
qui sum incwage, detail
local p1 = `r(p1)'
local p95 = `r(p95)'
replace income_clean = `p95' if incwage >= `p95'

drop incwage 

export delimited "/Users/vs3041/Dropbox (Princeton)/Irreducible Error/LTP_final/ACS_clean_LTP_final.csv", nolabel replace

