import delimited "C:\Users\xtang2\Downloads\xiaorui\project\data\output\df_fin_reg.csv", clear 
encode country, gen(country_id)
encode region, gen(region_id)

xtset country_id year

// define variables 
// (cate1, cate2)
replace fis_agreement_general_gpt_ft = . if fis_agreement_gpt_ft == .
gen fis_agreement_stance = 0 if v181=="major difference"
replace fis_agreement_stance = 1 if v181 == "some difference"
replace fis_agreement_stance = 2 if v181 == "minor difference"
replace fis_agreement_stance = 3 if v181== "no difference"
rename v182 fis_relative_stance

replace mon_agreement_general_gpt_ft = . if mon_agreement_gpt_ft == .
gen mon_agreement_stance = 0 if v169=="major difference"
replace mon_agreement_stance = 1 if v169 == "some difference"
replace mon_agreement_stance = 2 if v169 == "minor difference"
replace mon_agreement_stance = 3 if v169 == "no difference"
rename v170 mon_relative_stance

gen agreement_gpt_ft = 1 if mon_agreement_general_gpt_ft==1 | fis_agreement_general_gpt_ft==1
replace agreement_gpt_ft = 0 if mon_agreement_general_gpt_ft==0 | fis_agreement_general_gpt_ft==0

encode policy_mix_buff, gen(policy_mix_buff_id)

// controls
gen ln_gdp = log(ppp_gdp)
replace ae  = 0 if ae == .
replace emde  = 0 if emde == .
replace lic = 0 if lic == .
replace fuel = 0 if fuel==.
replace commodity_exc_fuel= 0 if commodity_exc_fuel==.
rename pallfnfindexq comm_price
gen commodity_exporter = commodity_exc_fuel + fuel >0
replace inprogram_after = "1" if inprogram_after=="True"
replace inprogram_after = "0" if inprogram_after=="False"
destring inprogram_after, replace
replace ta = "1" if ta=="True"
replace ta = "0" if ta=="False"
destring ta, replace
replace ta_after = "1" if ta_after=="True"
replace ta_after = "0" if ta_after=="False"
destring ta_after, replace
replace fsap = "1" if fsap=="True"
replace fsap = "0" if fsap=="False"
destring fsap, replace
replace fsap_after = "1" if fsap_after=="True"
replace fsap_after = "0" if fsap_after=="False"
destring fsap_after, replace
gen system_president = 0 if system !=""
replace system_president = 1 if system == "Presidential"
gen system_ass_elec_pres = 0 if system !=""
replace system_ass_elec_pres = 1 if system == "Assembly-Elected President"
gen ext_debt_gdp = ext_debt_gross/ppp_gdp*100000000

gen MtFt = 0 if policy_mix_staff !=""
replace MtFt = 1 if policy_mix_staff == "MtFt"
gen MtFn = 0 if policy_mix_staff !=""
replace MtFn = 1 if policy_mix_staff == "MtFn"
gen MtFl = 0 if policy_mix_staff !=""
replace MtFl = 1 if policy_mix_staff == "MtFl"
gen MnFt = 0 if policy_mix_staff !=""
replace MnFt = 1 if policy_mix_staff == "MnFt"
gen MnFl = 0 if policy_mix_staff !=""
replace MnFl = 1 if policy_mix_staff == "MnFl"
gen MlFt = 0 if policy_mix_staff !=""
replace MlFt = 1 if policy_mix_staff == "MlFt"
gen MlFn = 0 if policy_mix_staff !=""
replace MlFn = 1 if policy_mix_staff == "MlFn"
gen MlFl = 0 if policy_mix_staff !=""
replace MlFl = 1 if policy_mix_staff == "MlFl"

// summary statistics
global agreement_gpt  "agreement_gpt agreement_gpt_monetary agreement_gpt_fiscal agreement_gpt_external agreement_gpt_financial agreement_gpt_real"
global agreement_mon "mon_agreement_general_gpt_ft mon_agreement_stance mon_relative_stance"
global agreement_fis "fis_agreement_general_gpt_ft fis_agreement_stance fis_relative_stance"

global agreement_reg1 "agreement_gpt mon_agreement_stance fis_agreement_stance"
global agreement_reg2_dummy "agreement_gpt_ft mon_agreement_general_gpt_ft fis_agreement_general_gpt_ft"

sum $agreement_gpt
sum $agreement_mon
sum $agreement_fis

// IMF program
est clear
foreach y of global agreement_reg1 {
	local temp = substr("`y'", 1, 15)
	reg `y' inprogram i.year
	est store a1_`temp'
	reg `y' inprogram inprogram_after i.year if inprogram_ever=="True"
	est store a2_`temp'
	reg `y' ta i.year
	est store a3_`temp'
	reg `y' ta ta_after i.year if ta_ever=="True"
	est store a4_`temp'
	reg `y' fsap i.year
	est store a5_`temp'
	reg `y' fsap fsap_after i.year if fsap_ever=="True"
	est store a6_`temp'
}
foreach y of global agreement_reg2_dummy {
	local temp = substr("`y'", 1, 15)
	probit `y' inprogram i.year
	est store a7_`temp'
	probit `y' inprogram inprogram_after i.year if inprogram_ever=="True"
	est store a8_`temp'
	probit `y' ta i.year
	est store a9_`temp'
	probit `y' ta ta_after i.year if ta_ever=="True"
	est store a10_`temp'
	probit `y' fsap i.year
	est store a5_`temp'
	probit `y' fsap fsap_after i.year if fsap_ever=="True"
	est store a6_`temp'
}

// reg agreement_gpt_financial fsap i.year
// reg agreement_gpt_financial fsap fsap_after i.year if fsap_ever=="True"
esttab a* using test2i.csv, b(%9.4f) se(%9.4f) r2(4) star(* 0.10 ** 0.05 *** 0.01) scalars(N r2_p r2)
	
// country characteristics
est clear
foreach y of global agreement_reg1 {
	local temp = substr("`y'", 1, 15)
	reg `y' ae emde i.year
	est store a1_`temp'
	reg `y' ln_gdp i.year
	est store a2_`temp'
	reg `y' kaopen i.year
	est store a3_`temp'
	reg `y' fixed_currency i.year
	est store a4_`temp'
	reg `y' inflationtarget monetarytarget i.year
	est store a6_`temp'
	reg `y' ae emde ln_gdp kaopen fixed_currency inflationtarget monetarytarget i.year inprogram
	est store a5_`temp'
}

foreach y of global agreement_reg2_dummy {
	local temp = substr("`y'", 1, 15)
	probit `y' ae emde i.year
	est store a1_`temp'
	probit `y' ln_gdp i.year
	est store a2_`temp'
	probit `y' kaopen i.year
	est store a3_`temp'
	probit `y' fixed_currency i.year
	est store a4_`temp'
	probit `y' inflationtarget monetarytarget i.year
	est store a6_`temp'
	probit `y' ae emde ln_gdp kaopen fixed_currency inflationtarget monetarytarget i.year inprogram
	est store a5_`temp'
}

esttab a* using test1f.csv, b(%9.4f) se(%9.4f) r2(4) star(* 0.10 ** 0.05 *** 0.01) scalars(N r2 r2_p)


// commodity exports
est clear
foreach y of global agreement_reg1 {
	local temp = substr("`y'", 1, 15)
// 	reg `y' c.commodity_exporter##c.comm_price 
// 	est store a1_`temp'
	reg `y' c.commodity_exporter##c.comm_price inprogram 
	est store a2_`temp'
}
foreach y of global agreement_reg2_dummy {
	local temp = substr("`y'", 1, 15)
// 	probit `y' c.commodity_exporter##c.comm_price 
// 	est store a1_`temp'
	probit `y' c.commodity_exporter##c.comm_price inprogram 
	est store a2_`temp'
}
esttab a* using test3g.csv, b(%9.4f) se(%9.4f) r2(4) star(* 0.10 ** 0.05 *** 0.01) scalars(N r2 r2_p)

gen election_year = 0 if election_years_left!=.
replace election_year = 1 if election_years_left==0
// political variables
est clear
foreach y of global agreement_reg1 {
	local temp = substr("`y'", 1, 15)
	reg `y' allhouse i.year 
	est store a1_`temp'
	reg `y' system_president i.year 
	est store a2_`temp'
	reg `y' system_ass_elec_pres i.year 
	est store a5_`temp'
	reg `y' election_years_left i.year 
	est store a3_`temp' 
	reg `y' allhouse system_president system_ass_elec_pres election_years_left inprogram i.year 
	est store a4_`temp' 
	
}
foreach y of global agreement_reg2_dummy {
	local temp = substr("`y'", 1, 15)
	probit `y' allhouse i.year 
	est store a1_`temp'
	probit `y' system_president i.year 
	est store a2_`temp'
	probit `y' system_ass_elec_pres i.year 
	est store a5_`temp'
	probit `y' election_years_left i.year 
	est store a3_`temp' 
	probit `y' allhouse system_president system_ass_elec_pres election_years_left inprogram i.year 
	est store a4_`temp' 
	
}
esttab a* using test4h.csv, b(%9.4f) se(%9.4f) r2(4) star(* 0.10 ** 0.05 *** 0.01) scalars(N r2 r2_p)

// risks
est clear
foreach y of global agreement_reg1 {
	local temp = substr("`y'", 1, 15)
	reg `y' vixcls 
	est store a1_`temp'
	reg `y' gepu_ppp
	est store a2_`temp'
	reg `y' usmpu
	est store a3_`temp'
	reg `y' epu i.year
	est store a4_`temp'
	reg `y' vixcls gepu_ppp usmpu epu inprogram
	est store a5_`temp'
}

foreach y of global agreement_reg2_dummy {
	local temp = substr("`y'", 1, 15)
	oprobit `y' vixcls 
	est store a1_`temp'
	oprobit `y' gepu_ppp
	est store a2_`temp'
	oprobit `y' usmpu
	est store a3_`temp'
	oprobit `y' epu i.year
	est store a4_`temp'
	oprobit `y' vixcls gepu_ppp usmpu epu inprogram
	est store a5_`temp'
}
esttab a* using test5c.csv, b(%9.4f) se(%9.4f) r2(4) star(* 0.10 ** 0.05 *** 0.01) scalars(N r2 r2_p)


// economic variables
est clear
foreach y of global agreement_reg1 {
	local temp = substr("`y'", 1, 15)
	reg `y' l.inflation ae emde inprogram  i.year
	est store a1_`temp'
	reg `y' l.d.ln_gdp ae emde inprogram  i.year
	est store a2_`temp'
	reg `y' l.unemployment ae emde inprogram  i.year
	est store a5_`temp'
	reg `y' l.govt_debt_net ae emde inprogram i.year
	est store a3_`temp'
	reg `y' l.ca_balance ae emde inprogram i.year
	est store a4_`temp'
	reg `y' l.d_neer ae emde inprogram i.year
	est store a6_`temp'
}
foreach y of global agreement_reg2_dummy {
	local temp = substr("`y'", 1, 15)
	probit `y' l.inflation ae emde inprogram  i.year
	est store a1_`temp'
	probit `y' l.d.ln_gdp ae emde inprogram  i.year
	est store a2_`temp'
	probit `y' l.unemployment ae emde inprogram  i.year
	est store a5_`temp'
	probit `y' l.govt_debt_net ae emde inprogram i.year
	est store a3_`temp'
	probit `y' l.ca_balance ae emde inprogram i.year
	est store a4_`temp'
	probit `y' l.d_neer ae emde inprogram i.year
	est store a6_`temp'
}
esttab a* using test6f.csv, b(%9.4f) se(%9.4f) r2(4) star(* 0.10 ** 0.05 *** 0.01) scalars(N r2 r2_p)


// policy stance
est clear
foreach y of global agreement_reg1 {
	local temp = substr("`y'", 1, 15)
	reg `y' MtFt MtFn MtFl MnFt MnFl MlFl MlFn MlFt i.year
	est store a6_`temp'
}
foreach y of global agreement_reg2_dummy {
	local temp = substr("`y'", 1, 15)
	probit `y' MtFt MtFn MtFl MnFt MnFl MlFl MlFn MlFt i.year
	est store a6_`temp'
}
esttab a* using test7b.csv, b(%9.4f) se(%9.4f) r2(4) star(* 0.10 ** 0.05 *** 0.01) scalars(N r2 r2_p)


// implications - for later
// inflation in 2022
reg inflation l.agreement_gpt if year==2022
reg inflation l.agreement_gpt_ft if year==2022
reg inflation l.mon_agreement_stance if year==2022
reg inflation l.mon_agreement_general_gpt_ft if year==2022

// growth in 2020
reg d.ln_gdp l.agreement_gpt if year==2020
reg d.ln_gdp l.agreement_gpt_ft if year==2020
reg d.ln_gdp l.mon_agreement_stance if year==2020
reg d.ln_gdp l.mon_agreement_general_gpt_ft if year==2020
reg d.ln_gdp l.fis_agreement_stance if year==2020
reg d.ln_gdp l.fis_agreement_general_gpt_ft if year==2020


// archive
reg agreement_gpt_fiscal inprogram

reg mon_relative_stance l.inflation l.ppp_gdp l.unemployment i.year i.region

xtreg mon_agreement_stance l.inflation l.ppp_gdp l.unemployment i.year, fe
xtreg mon_agreement_general_gpt_ft l.inflation l.ppp_gdp l.unemployment i.year, fe