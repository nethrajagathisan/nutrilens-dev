"""
Nutrition knowledge base — 64 factual document chunks covering 16 topics.
Each entry: {"id": str, "topic": str, "text": str (3-6 sentences)}.
"""

_DOCS = [
    # ── Protein ────────────────────────────────────────────────────────────────
    {
        "id": "protein-001",
        "topic": "Protein",
        "text": (
            "The recommended daily allowance for protein is 0.8 grams per kilogram of body weight "
            "for sedentary adults. Athletes and people doing regular resistance training need between "
            "1.2 and 2.0 grams per kilogram. High-quality complete protein sources that contain all "
            "essential amino acids include eggs, chicken, fish, beef, dairy, and soy. Plant-based "
            "sources like lentils, chickpeas, quinoa, and tofu are excellent options for vegans but "
            "may need to be combined to achieve a complete amino acid profile."
        ),
    },
    {
        "id": "protein-002",
        "topic": "Protein",
        "text": (
            "Protein plays a critical role in muscle repair and growth after exercise. During "
            "resistance training, muscle fibres sustain micro-tears that require amino acids to "
            "rebuild stronger. Consuming 20-40 grams of protein within two hours after a workout "
            "maximises muscle protein synthesis. Leucine, an essential branched-chain amino acid "
            "found abundantly in whey and eggs, is the primary trigger for this process."
        ),
    },
    {
        "id": "protein-003",
        "topic": "Protein",
        "text": (
            "Plant-based protein sources can meet all human amino acid requirements when consumed "
            "in adequate variety throughout the day. Combining legumes with grains — such as rice "
            "and beans — provides a complete amino acid profile. Soy products like tempeh and edamame "
            "are among the few plant sources that are complete on their own. Seitan, made from wheat "
            "gluten, provides about 25 grams of protein per 100 grams but is low in lysine."
        ),
    },
    {
        "id": "protein-004",
        "topic": "Protein",
        "text": (
            "Excessive protein intake beyond 2.5 grams per kilogram per day offers no additional "
            "muscle-building benefit and may strain the kidneys in people with pre-existing kidney "
            "conditions. The body cannot store excess amino acids so surplus protein is converted to "
            "glucose or fat. Distributing protein evenly across meals — roughly 25-35 grams per meal "
            "— is more effective for muscle protein synthesis than eating it all at once."
        ),
    },
    # ── Carbohydrates ─────────────────────────────────────────────────────────
    {
        "id": "carbs-001",
        "topic": "Carbohydrates",
        "text": (
            "Carbohydrates are the body's primary and preferred energy source, providing 4 calories "
            "per gram. Simple carbohydrates like glucose and fructose are absorbed quickly and cause "
            "rapid blood sugar spikes. Complex carbohydrates such as oats, brown rice, and sweet "
            "potatoes are digested slowly and provide sustained energy. The recommended carbohydrate "
            "intake is 45-65 percent of total daily calories for most adults."
        ),
    },
    {
        "id": "carbs-002",
        "topic": "Carbohydrates",
        "text": (
            "The glycemic index ranks carbohydrate-containing foods on a scale of 0 to 100 based on "
            "how quickly they raise blood sugar. Foods with a GI below 55 are considered low-glycemic "
            "and include lentils, most fruits, and non-starchy vegetables. High-GI foods above 70 "
            "include white bread, white rice, and potatoes. Choosing low-GI foods helps maintain "
            "steady energy levels and may reduce the risk of type 2 diabetes."
        ),
    },
    {
        "id": "carbs-003",
        "topic": "Carbohydrates",
        "text": (
            "Dietary fibre is a type of complex carbohydrate that the body cannot digest. It passes "
            "through the digestive system largely intact and supports gut health by feeding beneficial "
            "bacteria. Soluble fibre found in oats, beans, and apples helps lower cholesterol and "
            "stabilise blood sugar. Insoluble fibre found in whole grains, nuts, and vegetables "
            "promotes regular bowel movements and prevents constipation."
        ),
    },
    {
        "id": "carbs-004",
        "topic": "Carbohydrates",
        "text": (
            "Carbohydrates are stored in muscles and the liver as glycogen, which serves as a readily "
            "available fuel source during exercise. The body can store approximately 400-500 grams of "
            "glycogen in total. Depleted glycogen stores lead to fatigue and reduced exercise "
            "performance. Consuming carbohydrates before and after exercise helps maintain glycogen "
            "levels and supports recovery."
        ),
    },
    # ── Healthy Fats ──────────────────────────────────────────────────────────
    {
        "id": "fats-001",
        "topic": "Healthy Fats",
        "text": (
            "Dietary fats provide 9 calories per gram, making them the most energy-dense macronutrient. "
            "Unsaturated fats — both monounsaturated and polyunsaturated — are considered heart-healthy "
            "and are found in olive oil, avocados, nuts, and fatty fish. Saturated fats found in butter, "
            "cheese, and red meat should be limited to less than 10 percent of total daily calories. "
            "Trans fats found in partially hydrogenated oils are the most harmful and should be avoided entirely."
        ),
    },
    {
        "id": "fats-002",
        "topic": "Healthy Fats",
        "text": (
            "Omega-3 fatty acids are essential polyunsaturated fats that the body cannot produce on "
            "its own. The three main types are ALA (found in flaxseeds and walnuts), EPA and DHA "
            "(found in fatty fish like salmon, mackerel, and sardines). EPA and DHA support brain "
            "function, reduce inflammation, and lower the risk of heart disease. Adults should aim "
            "for at least two servings of fatty fish per week or consider an algae-based supplement."
        ),
    },
    {
        "id": "fats-003",
        "topic": "Healthy Fats",
        "text": (
            "Avocados are one of the richest sources of monounsaturated fat, containing about 15 grams "
            "of fat per fruit, most of which is oleic acid. They also provide potassium, fibre, and "
            "vitamins K, C, and B6. Regular avocado consumption has been associated with improved "
            "cholesterol profiles and better nutrient absorption from other foods. Nuts such as almonds, "
            "walnuts, and pistachios provide healthy fats along with protein and micronutrients."
        ),
    },
    {
        "id": "fats-004",
        "topic": "Healthy Fats",
        "text": (
            "Omega-6 fatty acids are essential but are consumed in excess in typical Western diets. "
            "The ideal omega-6 to omega-3 ratio is between 1:1 and 4:1, but many people consume ratios "
            "of 15:1 or higher. Excess omega-6 from vegetable oils like soybean and corn oil can promote "
            "inflammation. Reducing processed food intake and increasing omega-3 rich foods helps restore "
            "a healthier balance between these essential fatty acids."
        ),
    },
    # ── Vitamins ──────────────────────────────────────────────────────────────
    {
        "id": "vitamins-001",
        "topic": "Vitamins",
        "text": (
            "Vitamin A is a fat-soluble vitamin essential for vision, immune function, and skin health. "
            "Preformed vitamin A (retinol) is found in liver, fish, eggs, and dairy products. Provitamin A "
            "carotenoids like beta-carotene are found in orange and green vegetables such as carrots, sweet "
            "potatoes, and spinach. The recommended daily intake is 900 micrograms for adult men and 700 "
            "micrograms for adult women."
        ),
    },
    {
        "id": "vitamins-002",
        "topic": "Vitamins",
        "text": (
            "Vitamin B12 is crucial for nerve function, red blood cell formation, and DNA synthesis. "
            "It is found almost exclusively in animal products including meat, fish, eggs, and dairy. "
            "Vegans are at high risk of B12 deficiency and should take a supplement or consume B12-fortified "
            "foods such as nutritional yeast, plant milks, and fortified cereals. Deficiency can cause "
            "irreversible nerve damage, fatigue, and megaloblastic anaemia."
        ),
    },
    {
        "id": "vitamins-003",
        "topic": "Vitamins",
        "text": (
            "Vitamin C is a water-soluble antioxidant that supports immune function, collagen synthesis, "
            "and iron absorption from plant-based foods. Excellent sources include citrus fruits, bell "
            "peppers, strawberries, broccoli, and kiwi. The recommended daily allowance is 90 mg for men "
            "and 75 mg for women, with smokers needing an additional 35 mg. Unlike fat-soluble vitamins, "
            "vitamin C cannot be stored in the body and needs to be consumed daily."
        ),
    },
    {
        "id": "vitamins-004",
        "topic": "Vitamins",
        "text": (
            "Vitamin D is synthesised in the skin when exposed to UVB sunlight and is also found in fatty "
            "fish, egg yolks, and fortified foods. It is essential for calcium absorption, bone health, "
            "and immune regulation. Deficiency is common in northern latitudes and among people with darker "
            "skin. The recommended intake is 600 IU per day for adults under 70 and 800 IU for those over "
            "70, though many experts suggest higher amounts of 1000-2000 IU."
        ),
    },
    # ── Minerals ──────────────────────────────────────────────────────────────
    {
        "id": "minerals-001",
        "topic": "Minerals",
        "text": (
            "Iron is an essential mineral that carries oxygen in the blood via haemoglobin. Heme iron from "
            "animal sources like red meat, liver, and shellfish is absorbed two to three times more "
            "efficiently than non-heme iron from plant sources. Plant-based iron in lentils, spinach, and "
            "fortified cereals can be enhanced by consuming vitamin C at the same meal. The RDA is 8 mg "
            "for adult men and 18 mg for premenopausal women."
        ),
    },
    {
        "id": "minerals-002",
        "topic": "Minerals",
        "text": (
            "Calcium is the most abundant mineral in the body and is critical for bone and teeth formation, "
            "muscle contraction, and nerve signalling. Dairy products are the richest sources, providing "
            "about 300 mg per cup of milk. Non-dairy sources include fortified plant milks, tofu made with "
            "calcium sulfate, broccoli, kale, and almonds. Adults need 1000 mg per day, increasing to "
            "1200 mg after age 50 for women and after age 70 for men."
        ),
    },
    {
        "id": "minerals-003",
        "topic": "Minerals",
        "text": (
            "Magnesium is involved in over 300 enzymatic reactions including energy production, muscle "
            "relaxation, and blood sugar regulation. Good sources include dark leafy greens, nuts, seeds, "
            "whole grains, and dark chocolate. The RDA is 420 mg for adult men and 320 mg for adult women. "
            "Magnesium deficiency is common and can cause muscle cramps, fatigue, and irregular heartbeat. "
            "Supplementation with magnesium glycinate or citrate has good bioavailability."
        ),
    },
    {
        "id": "minerals-004",
        "topic": "Minerals",
        "text": (
            "Zinc supports immune function, wound healing, protein synthesis, and taste perception. "
            "The richest food sources are oysters, red meat, poultry, beans, nuts, and whole grains. "
            "The RDA is 11 mg for adult men and 8 mg for adult women. Phytates in whole grains and "
            "legumes can inhibit zinc absorption, so vegetarians may need up to 50 percent more zinc. "
            "Potassium helps regulate fluid balance, muscle contractions, and blood pressure, with an "
            "adequate intake of 2600-3400 mg per day from bananas, potatoes, and leafy greens."
        ),
    },
    # ── Hydration ─────────────────────────────────────────────────────────────
    {
        "id": "hydration-001",
        "topic": "Hydration",
        "text": (
            "The general recommendation for daily water intake is about 3.7 litres for men and 2.7 litres "
            "for women from all beverages and food combined. About 20 percent of daily water intake comes "
            "from food, especially fruits and vegetables with high water content like watermelon and "
            "cucumbers. Individual needs vary based on body size, climate, physical activity, and health "
            "status. A simple guideline is to drink enough so that urine is pale yellow."
        ),
    },
    {
        "id": "hydration-002",
        "topic": "Hydration",
        "text": (
            "Early signs of dehydration include thirst, dark yellow urine, dry mouth, fatigue, and "
            "headache. Even mild dehydration of 1-2 percent body weight loss can impair cognitive "
            "function, mood, and physical performance. Severe dehydration can cause dizziness, rapid "
            "heartbeat, confusion, and requires medical attention. Older adults are at higher risk "
            "because the thirst sensation diminishes with age."
        ),
    },
    {
        "id": "hydration-003",
        "topic": "Hydration",
        "text": (
            "Water plays a key role in metabolism by serving as the medium for virtually all biochemical "
            "reactions in the body. Studies show that drinking 500 ml of water can temporarily boost "
            "metabolic rate by 24-30 percent for about 30-40 minutes. Drinking water before meals may "
            "also reduce appetite and calorie intake, supporting weight management. Cold water requires "
            "the body to expend a small amount of energy to warm it to body temperature."
        ),
    },
    {
        "id": "hydration-004",
        "topic": "Hydration",
        "text": (
            "Electrolytes — sodium, potassium, magnesium, and chloride — are minerals that carry "
            "electrical charges and are essential for fluid balance and nerve function. During intense "
            "exercise lasting over an hour, electrolyte losses through sweat can be significant and "
            "should be replaced. Sports drinks can help during prolonged exercise but are unnecessary "
            "for moderate activity. Coconut water is a natural source of potassium and electrolytes."
        ),
    },
    # ── Calories ──────────────────────────────────────────────────────────────
    {
        "id": "calories-001",
        "topic": "Calories",
        "text": (
            "A calorie is a unit of energy. In nutrition, one kilocalorie (kcal or Calorie with a "
            "capital C) equals the energy needed to raise one kilogram of water by one degree Celsius. "
            "Carbohydrates and protein provide 4 kcal per gram, fat provides 9 kcal per gram, and "
            "alcohol provides 7 kcal per gram. Understanding calorie density helps make informed "
            "food choices for weight management."
        ),
    },
    {
        "id": "calories-002",
        "topic": "Calories",
        "text": (
            "Basal Metabolic Rate (BMR) is the number of calories the body burns at complete rest to "
            "maintain basic life functions like breathing, circulation, and cell production. The "
            "Mifflin-St Jeor equation estimates BMR as (10 × weight in kg) + (6.25 × height in cm) "
            "- (5 × age in years) + 5 for men or -161 for women. BMR typically accounts for 60-75 "
            "percent of total daily energy expenditure."
        ),
    },
    {
        "id": "calories-003",
        "topic": "Calories",
        "text": (
            "Total Daily Energy Expenditure (TDEE) is BMR multiplied by an activity factor: 1.2 for "
            "sedentary, 1.375 for lightly active, 1.55 for moderately active, 1.725 for very active, "
            "and 1.9 for extremely active individuals. Eating above TDEE leads to weight gain (caloric "
            "surplus), while eating below TDEE causes weight loss (caloric deficit). A deficit of "
            "approximately 500 kcal per day results in roughly 0.45 kg of fat loss per week."
        ),
    },
    {
        "id": "calories-004",
        "topic": "Calories",
        "text": (
            "A caloric surplus means consuming more calories than the body expends, which is necessary "
            "for muscle gain when combined with resistance training. A moderate surplus of 250-500 kcal "
            "per day is recommended for lean muscle gain to minimise fat accumulation. A caloric deficit "
            "is required for fat loss, but going too low — below 1200 kcal for women or 1500 kcal for "
            "men — can slow metabolism and cause nutrient deficiencies."
        ),
    },
    # ── Weight Loss ───────────────────────────────────────────────────────────
    {
        "id": "weightloss-001",
        "topic": "Weight Loss",
        "text": (
            "Sustainable weight loss requires a moderate caloric deficit of 500-750 kcal per day, "
            "resulting in a loss of 0.5-0.75 kg per week. Crash diets with very low calorie intake "
            "lead to muscle loss, metabolic adaptation, and are rarely sustained long-term. The body "
            "adapts to prolonged restriction by lowering BMR, a phenomenon known as metabolic "
            "adaptation or adaptive thermogenesis. Gradual, consistent changes to diet and activity "
            "are more effective than extreme approaches."
        ),
    },
    {
        "id": "weightloss-002",
        "topic": "Weight Loss",
        "text": (
            "Preserving muscle mass during weight loss is critical for maintaining metabolic rate and "
            "functional strength. High protein intake of 1.6-2.2 grams per kilogram, combined with "
            "resistance training at least twice per week, helps preserve lean mass during a deficit. "
            "Losing weight too rapidly — more than 1 kg per week — significantly increases the risk "
            "of muscle loss. Sleep quality and stress management also play important roles in body "
            "composition during weight loss."
        ),
    },
    {
        "id": "weightloss-003",
        "topic": "Weight Loss",
        "text": (
            "Common weight loss mistakes include skipping meals, eliminating entire food groups, "
            "relying solely on the scale, and not tracking calories accurately. Many people "
            "underestimate their calorie intake by 20-50 percent. Liquid calories from sugary drinks, "
            "alcohol, and specialty coffee beverages are often overlooked. Consistent food logging "
            "has been shown in studies to double weight loss success rates compared to not tracking."
        ),
    },
    {
        "id": "weightloss-004",
        "topic": "Weight Loss",
        "text": (
            "A safe rate of weight loss is 0.5-1 kg per week for most people. More rapid weight loss "
            "may be appropriate under medical supervision for individuals with a BMI over 30. Weight "
            "loss is not always linear — water retention, menstrual cycles, and sodium intake cause "
            "daily fluctuations. Tracking weekly averages rather than daily weigh-ins provides a "
            "more accurate picture of progress."
        ),
    },
    # ── Keto Diet ─────────────────────────────────────────────────────────────
    {
        "id": "keto-001",
        "topic": "Keto Diet",
        "text": (
            "The ketogenic diet is a high-fat, very low-carbohydrate diet that typically limits carbs "
            "to 20-50 grams per day. When carbohydrates are sufficiently restricted, the body enters "
            "a metabolic state called ketosis where the liver converts fatty acids into ketone bodies "
            "for fuel. This metabolic shift usually takes 2-4 days of strict carbohydrate restriction. "
            "The standard macronutrient ratio is roughly 70-75 percent fat, 20-25 percent protein, "
            "and 5-10 percent carbohydrates."
        ),
    },
    {
        "id": "keto-002",
        "topic": "Keto Diet",
        "text": (
            "Foods commonly consumed on a keto diet include meat, fatty fish, eggs, butter, cheese, "
            "nuts, seeds, avocados, and low-carb vegetables like spinach, kale, and broccoli. Foods "
            "to avoid include grains, sugar, most fruits, legumes, potatoes, and processed foods. "
            "Coconut oil, olive oil, and MCT oil are popular fat sources. Hidden carbohydrates in "
            "sauces, condiments, and processed meats can inadvertently break ketosis."
        ),
    },
    {
        "id": "keto-003",
        "topic": "Keto Diet",
        "text": (
            "Potential benefits of the keto diet include rapid initial weight loss (mostly water), "
            "reduced appetite due to ketone production, improved blood sugar control in type 2 "
            "diabetes, and possible benefits for neurological conditions like epilepsy. Some people "
            "report improved mental clarity and sustained energy once adapted. The diet has been used "
            "therapeutically for drug-resistant epilepsy in children since the 1920s."
        ),
    },
    {
        "id": "keto-004",
        "topic": "Keto Diet",
        "text": (
            "Risks and side effects of the keto diet include the 'keto flu' during the first week — "
            "headache, fatigue, nausea, and irritability caused by electrolyte shifts and glycogen "
            "depletion. Long-term risks may include kidney stones, nutrient deficiencies (particularly "
            "fibre, vitamin C, and potassium), elevated LDL cholesterol in some people, and liver "
            "stress. The adaptation period typically lasts 2-6 weeks before full metabolic efficiency "
            "is reached."
        ),
    },
    # ── Vegan Diet ────────────────────────────────────────────────────────────
    {
        "id": "vegan-001",
        "topic": "Vegan Diet",
        "text": (
            "Vitamin B12 is the most critical nutrient for vegans to supplement because it is not "
            "reliably found in any plant foods. The recommended intake is 2.4 micrograms per day, "
            "which can be obtained from a daily supplement or B12-fortified foods consumed at least "
            "twice daily. Deficiency develops slowly over years and can cause irreversible "
            "neurological damage. All major dietetic associations recommend B12 supplementation "
            "for vegans."
        ),
    },
    {
        "id": "vegan-002",
        "topic": "Vegan Diet",
        "text": (
            "Protein combining — eating complementary plant proteins at the same meal — was once "
            "considered essential but modern nutrition science shows it is not necessary at every "
            "meal. As long as a variety of protein-rich plant foods are eaten throughout the day, "
            "the body can obtain all essential amino acids. Key vegan protein sources include "
            "lentils, chickpeas, tofu, tempeh, seitan, edamame, hemp seeds, and quinoa."
        ),
    },
    {
        "id": "vegan-003",
        "topic": "Vegan Diet",
        "text": (
            "Iron absorption from plant foods (non-heme iron) is significantly lower than from animal "
            "sources (heme iron). Vegans can improve absorption by pairing iron-rich foods like "
            "spinach, lentils, and fortified cereals with vitamin C sources such as citrus fruits "
            "or bell peppers. Avoiding tea and coffee with iron-rich meals also helps, as tannins "
            "inhibit absorption. Vegans often need almost twice the RDA of iron."
        ),
    },
    {
        "id": "vegan-004",
        "topic": "Vegan Diet",
        "text": (
            "Calcium can be obtained without dairy through fortified plant milks (which provide "
            "similar amounts to cow's milk when fortified), tofu set with calcium sulfate, kale, "
            "bok choy, broccoli, and almonds. The RDA of 1000 mg per day is achievable on a vegan "
            "diet with planning. Oxalates in spinach and Swiss chard reduce calcium bioavailability, "
            "so these should not be relied upon as primary calcium sources."
        ),
    },
    # ── Fiber ─────────────────────────────────────────────────────────────────
    {
        "id": "fiber-001",
        "topic": "Fiber",
        "text": (
            "Soluble fibre dissolves in water to form a gel-like substance that slows digestion and "
            "helps lower blood cholesterol and blood glucose levels. Major sources include oats, "
            "barley, beans, lentils, apples, and citrus fruits. Psyllium husk is a concentrated "
            "soluble fibre supplement commonly used to improve regularity. Soluble fibre also acts "
            "as a prebiotic, feeding beneficial gut bacteria."
        ),
    },
    {
        "id": "fiber-002",
        "topic": "Fiber",
        "text": (
            "Insoluble fibre does not dissolve in water and adds bulk to stool, promoting regular "
            "bowel movements and preventing constipation. It is found in whole wheat, wheat bran, "
            "nuts, beans, cauliflower, and the skins of many fruits and vegetables. Insoluble fibre "
            "also helps food pass more quickly through the stomach and intestines. Most plant foods "
            "contain both types of fibre in varying proportions."
        ),
    },
    {
        "id": "fiber-003",
        "topic": "Fiber",
        "text": (
            "A healthy gut microbiome is closely linked to adequate fibre intake. Fibre fermentation "
            "by gut bacteria produces short-chain fatty acids (SCFAs) like butyrate, which nourish "
            "colon cells and reduce inflammation. A diverse diet rich in different fibre sources "
            "promotes microbial diversity, which is associated with better immune function and lower "
            "risk of chronic disease. Sudden large increases in fibre intake can cause bloating and "
            "gas, so changes should be gradual."
        ),
    },
    {
        "id": "fiber-004",
        "topic": "Fiber",
        "text": (
            "The recommended daily fibre intake is 25 grams for women and 38 grams for men, but "
            "most people consume only about half that amount. High-fibre foods promote satiety and "
            "can help with weight management by increasing the feeling of fullness after meals. "
            "Increasing fibre intake should be accompanied by adequate water consumption to prevent "
            "digestive discomfort. Whole foods are preferred over fibre supplements for maximum benefit."
        ),
    },
    # ── Meal Timing ───────────────────────────────────────────────────────────
    {
        "id": "mealtiming-001",
        "topic": "Meal Timing",
        "text": (
            "Eating breakfast within an hour of waking has been associated with improved concentration, "
            "better blood sugar regulation throughout the day, and reduced tendency to overeat later. "
            "A protein-rich breakfast of 20-30 grams of protein helps maintain muscle mass and controls "
            "appetite more effectively than a carbohydrate-heavy breakfast. However, individual responses "
            "to breakfast vary and some people function well without it."
        ),
    },
    {
        "id": "mealtiming-002",
        "topic": "Meal Timing",
        "text": (
            "Pre-workout nutrition should include easily digestible carbohydrates consumed 30-60 minutes "
            "before exercise to top up glycogen stores. Post-workout, consuming a combination of protein "
            "and carbohydrates within two hours supports muscle recovery and glycogen replenishment. "
            "The post-exercise 'anabolic window' is wider than previously thought — total daily protein "
            "intake matters more than exact timing for most recreational exercisers."
        ),
    },
    {
        "id": "mealtiming-003",
        "topic": "Meal Timing",
        "text": (
            "Intermittent fasting (IF) involves cycling between periods of eating and fasting. Common "
            "protocols include the 16:8 method (16 hours fasting, 8 hours eating) and the 5:2 method "
            "(eating normally five days, restricting to 500-600 kcal two days). Research suggests IF "
            "can be as effective as continuous calorie restriction for weight loss. Benefits may include "
            "improved insulin sensitivity and cellular autophagy, but it is not suitable for everyone."
        ),
    },
    {
        "id": "mealtiming-004",
        "topic": "Meal Timing",
        "text": (
            "Circadian eating aligns food intake with the body's natural biological clock. Research shows "
            "that eating most calories earlier in the day — front-loading meals at breakfast and lunch — "
            "may improve weight management and metabolic health. Late-night eating is associated with "
            "poorer blood sugar control and increased fat storage. The gut microbiome also follows "
            "circadian rhythms and functions best with consistent meal times."
        ),
    },
    # ── BMI ───────────────────────────────────────────────────────────────────
    {
        "id": "bmi-001",
        "topic": "BMI",
        "text": (
            "Body Mass Index (BMI) is calculated as weight in kilograms divided by height in metres "
            "squared. A BMI of 18.5 to 24.9 is considered normal weight, 25.0 to 29.9 is overweight, "
            "and 30.0 or above is classified as obese. Below 18.5 is considered underweight. BMI is "
            "a screening tool used to identify possible weight problems but does not directly "
            "measure body fat percentage."
        ),
    },
    {
        "id": "bmi-002",
        "topic": "BMI",
        "text": (
            "BMI has significant limitations as a health indicator. It does not distinguish between "
            "muscle mass and fat mass, so muscular athletes often register as overweight despite having "
            "low body fat. It also does not account for fat distribution — abdominal fat (measured by "
            "waist circumference) is a stronger predictor of cardiovascular risk than BMI alone. "
            "Age, sex, and ethnicity also affect the relationship between BMI and health risk."
        ),
    },
    {
        "id": "bmi-003",
        "topic": "BMI",
        "text": (
            "A healthy BMI range of 18.5-24.9 is associated with the lowest risk of chronic diseases "
            "including type 2 diabetes, cardiovascular disease, and certain cancers. Maintaining a "
            "healthy BMI typically requires balanced nutrition and regular physical activity of at "
            "least 150 minutes of moderate exercise per week. Small changes in BMI even within the "
            "normal range can have meaningful health effects."
        ),
    },
    {
        "id": "bmi-004",
        "topic": "BMI",
        "text": (
            "To calculate BMI, divide body weight in kilograms by the square of height in metres. "
            "For example, a person weighing 70 kg and measuring 1.75 m tall has a BMI of 70 / (1.75 "
            "× 1.75) = 22.9, which falls in the normal range. Online BMI calculators and health apps "
            "can automate this. BMI should be considered alongside other metrics like waist-to-hip "
            "ratio, body fat percentage, and blood biomarkers for a complete health assessment."
        ),
    },
    # ── Exercise and Nutrition ────────────────────────────────────────────────
    {
        "id": "exercise-001",
        "topic": "Exercise and Nutrition",
        "text": (
            "Carbohydrate loading is a strategy used by endurance athletes before long events. It "
            "involves eating a high-carbohydrate diet (8-12 grams per kg body weight) in the 1-3 days "
            "before competition to maximise glycogen stores. This is most beneficial for events lasting "
            "longer than 90 minutes, such as marathons and long-distance cycling. For shorter workouts, "
            "normal carbohydrate intake is sufficient."
        ),
    },
    {
        "id": "exercise-002",
        "topic": "Exercise and Nutrition",
        "text": (
            "Protein timing around exercise supports muscle repair and growth. Consuming 20-40 grams "
            "of protein within a few hours after resistance training stimulates muscle protein synthesis. "
            "Whey protein is rapidly absorbed and is a popular post-workout choice, while casein is "
            "slower-digesting and may be beneficial before sleep. For most people, spreading protein "
            "intake evenly across 3-4 meals per day is more important than precise timing."
        ),
    },
    {
        "id": "exercise-003",
        "topic": "Exercise and Nutrition",
        "text": (
            "Hydration during exercise is critical for performance and safety. During moderate exercise, "
            "the body loses 0.5-1.5 litres of sweat per hour. Drinking 150-250 ml every 15-20 minutes "
            "during exercise helps maintain hydration. For sessions over one hour, a sports drink with "
            "electrolytes and carbohydrates may be beneficial. Weighing yourself before and after "
            "exercise reveals fluid loss — aim to replace 150 percent of the lost weight in fluids."
        ),
    },
    {
        "id": "exercise-004",
        "topic": "Exercise and Nutrition",
        "text": (
            "Recovery nutrition focuses on replenishing glycogen stores, repairing muscle tissue, and "
            "rehydrating. The optimal recovery meal or snack should include both carbohydrates and "
            "protein in a roughly 3:1 ratio. Examples include chocolate milk, a banana with peanut "
            "butter, or yoghurt with granola. Anti-inflammatory foods like tart cherry juice and "
            "omega-3 rich fish may help reduce exercise-induced muscle soreness."
        ),
    },
    # ── Gut Health ────────────────────────────────────────────────────────────
    {
        "id": "guthealth-001",
        "topic": "Gut Health",
        "text": (
            "Probiotics are live beneficial bacteria that, when consumed in adequate amounts, confer "
            "health benefits. Common probiotic strains include Lactobacillus and Bifidobacterium, "
            "found in yoghurt, kefir, and probiotic supplements. Regular consumption may improve "
            "digestive comfort, reduce antibiotic-associated diarrhoea, and support immune function. "
            "The effectiveness of probiotics is strain-specific, so not all products offer the same "
            "benefits."
        ),
    },
    {
        "id": "guthealth-002",
        "topic": "Gut Health",
        "text": (
            "Prebiotics are non-digestible fibres that feed the beneficial bacteria already living "
            "in the gut. Major prebiotic-rich foods include garlic, onions, leeks, asparagus, bananas, "
            "oats, and chicory root. Unlike probiotics, prebiotics are not living organisms and are "
            "more stable during food processing and storage. A diet rich in diverse plant foods "
            "naturally provides ample prebiotic fibre."
        ),
    },
    {
        "id": "guthealth-003",
        "topic": "Gut Health",
        "text": (
            "Fermented foods undergo a process where natural bacteria feed on sugars and starches, "
            "creating lactic acid. Examples include kimchi, sauerkraut, miso, tempeh, kombucha, and "
            "traditional pickles. These foods provide both live bacteria and compounds that support "
            "gut barrier integrity. Regular consumption of fermented foods has been shown to increase "
            "microbial diversity, which is a marker of gut health."
        ),
    },
    {
        "id": "guthealth-004",
        "topic": "Gut Health",
        "text": (
            "The gut microbiome contains trillions of bacteria that play a role in digestion, vitamin "
            "synthesis (especially B vitamins and vitamin K), and immune regulation. About 70 percent "
            "of the immune system resides in the gut-associated lymphoid tissue. A diverse microbiome "
            "is linked to lower rates of allergies, autoimmune conditions, and metabolic diseases. "
            "Factors that harm microbiome diversity include excessive antibiotic use, highly processed "
            "diets, and chronic stress."
        ),
    },
    # ── Sugar ─────────────────────────────────────────────────────────────────
    {
        "id": "sugar-001",
        "topic": "Sugar",
        "text": (
            "Natural sugars occur inherently in whole foods like fruits (fructose) and dairy (lactose) "
            "and come packaged with fibre, vitamins, and minerals that moderate absorption. Added "
            "sugars are those introduced during processing or preparation and include table sugar, "
            "high-fructose corn syrup, honey, and agave nectar. The body metabolises natural and added "
            "sugars identically, but whole food sources deliver more nutrients per calorie."
        ),
    },
    {
        "id": "sugar-002",
        "topic": "Sugar",
        "text": (
            "High-glycemic foods and drinks that contain large amounts of added sugar cause rapid blood "
            "glucose spikes followed by sharp insulin responses and energy crashes. These glycemic "
            "swings can increase hunger, promote fat storage, and over time contribute to insulin "
            "resistance and type 2 diabetes. Pairing sugars with protein, fat, or fibre slows "
            "absorption and minimises blood sugar fluctuations."
        ),
    },
    {
        "id": "sugar-003",
        "topic": "Sugar",
        "text": (
            "Hidden sugars are found in many foods not typically considered sweet, including bread, "
            "pasta sauces, salad dressings, flavoured yoghurt, granola bars, and ketchup. Sugar "
            "appears on ingredient labels under more than 60 different names, including sucrose, "
            "maltose, dextrose, corn syrup, and cane juice. Reading nutrition labels carefully is "
            "the most effective way to identify hidden sugar sources."
        ),
    },
    {
        "id": "sugar-004",
        "topic": "Sugar",
        "text": (
            "The World Health Organization recommends that added sugars constitute less than 10 percent "
            "of total daily energy intake, with a further reduction to below 5 percent — approximately "
            "25 grams or 6 teaspoons per day — for additional health benefits. The average American "
            "consumes about 77 grams of added sugar daily, more than three times the recommended limit. "
            "Reducing added sugar intake is one of the most impactful dietary changes for overall health."
        ),
    },
]

_DOCS.extend([
    {
        "id": "dietguidelines-001",
        "topic": "Diet Guidelines",
        "text": (
            "A balanced plate is a practical way to structure meals for most adults. Half the plate "
            "should come from vegetables and fruit, one quarter from lean protein, and one quarter from "
            "high-fibre carbohydrates such as brown rice, beans, or potatoes. Adding a source of healthy "
            "fat like olive oil, nuts, or avocado improves satiety and nutrient absorption. This approach "
            "supports weight management and helps cover macro- and micronutrient needs without rigid dieting."
        ),
    },
    {
        "id": "dietguidelines-002",
        "topic": "Diet Guidelines",
        "text": (
            "Diet quality matters as much as calorie quantity. Meals built around minimally processed foods "
            "tend to provide more fibre, vitamins, minerals, and protein per calorie than ultra-processed foods. "
            "A practical guideline is to prioritise foods with a short ingredient list and include protein and "
            "produce at most meals. This improves satiety, blood sugar control, and long-term adherence."
        ),
    },
    {
        "id": "dietguidelines-003",
        "topic": "Diet Guidelines",
        "text": (
            "Meal planning becomes more effective when it matches the person's goal. For fat loss, a modest "
            "calorie deficit with high protein and high-fibre foods is usually the most sustainable option. For "
            "performance or muscle gain, meals should include enough carbohydrates to support training and enough "
            "protein to support recovery. The best diet is one that fits the user's medical needs, culture, and routine."
        ),
    },
    {
        "id": "dietguidelines-004",
        "topic": "Diet Guidelines",
        "text": (
            "Consistency beats perfection in nutrition. Missing one healthy meal does not ruin progress, just as "
            "one ideal meal does not transform health. People make better long-term progress when they focus on "
            "repeatable habits such as eating protein at each meal, drinking enough water, and logging intake honestly. "
            "These behaviours produce more durable results than short bursts of strict dieting."
        ),
    },
    {
        "id": "fitnesstips-001",
        "topic": "Fitness Tips",
        "text": (
            "Progressive overload is the main principle behind fitness improvement. Whether the goal is strength, "
            "muscle gain, or endurance, the body adapts only when training stress gradually increases over time. "
            "This can come from adding weight, repetitions, sets, distance, or training frequency. Recovery, sleep, "
            "and nutrition need to increase alongside training demand for progress to continue."
        ),
    },
    {
        "id": "fitnesstips-002",
        "topic": "Fitness Tips",
        "text": (
            "Most adults benefit from a mix of resistance training, cardio, and daily movement. General public-health "
            "guidelines recommend at least 150 minutes of moderate aerobic exercise per week plus muscle-strengthening "
            "work on two or more days. Resistance training helps preserve muscle mass during weight loss and improves "
            "glucose control, bone density, and metabolic health."
        ),
    },
    {
        "id": "fitnesstips-003",
        "topic": "Fitness Tips",
        "text": (
            "Recovery is where adaptation actually happens. Training hard without enough sleep, hydration, and dietary "
            "energy often leads to stalled performance, frequent soreness, and elevated injury risk. Most adults need "
            "7 to 9 hours of sleep per night, and athletes or highly active people often need even more recovery focus. "
            "Protein, carbohydrates, and fluids after exercise all support a faster return to baseline."
        ),
    },
    {
        "id": "fitnesstips-004",
        "topic": "Fitness Tips",
        "text": (
            "Low-intensity movement outside formal workouts still matters. Walking more, taking stairs, and reducing "
            "sedentary time can significantly increase total daily energy expenditure and improve cardiovascular health. "
            "For many people trying to lose weight, non-exercise activity is easier to sustain than adding long workouts. "
            "Combining regular movement with structured exercise produces the best overall health outcomes."
        ),
    },
])

KNOWLEDGE_BASE = _DOCS
