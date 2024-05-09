library(tidyverse)
library(ggplot2)
library(ggridges)

directory_path <- "/Users/vs3041/Dropbox (Princeton)/Irreducible Error"

setwd(directory_path)

results_quartile_resolution <- read_csv(paste("LTP_final", "results_log_quart.csv", sep = "/")) %>%
  mutate(resolution = "Quartile")

results_median_resolution <- read_csv(paste("LTP_final", "results_log_median.csv", sep = "/")) %>%
  mutate(resolution = "Median")

results_decile_resolution <- read_csv(paste("LTP_final", "results_log_dec.csv", sep = "/")) %>%
  mutate(resolution = "Decile")

results_from_ACS <- rbind(results_quartile_resolution, results_median_resolution, results_decile_resolution)

# to get the correct order in facet plot
results_from_ACS$factor_for_facet <- factor(results_from_ACS$resolution, levels=c("Median", "Quartile","Decile"))


# median of densities 
# this plot is also where we get our resolution numbers
median_plot <- results_from_ACS %>%
  group_by(NUM_FEATURES, factor_for_facet) %>% 
  summarize(median_IR = median(IRREDUCIBLE_ERROR))

# plotting the distributions of IR at each number of features

ggplot(results_from_ACS, aes(x = IRREDUCIBLE_ERROR, y = as.factor(NUM_FEATURES))) +
  geom_density_ridges(jittered_points = F,
                      position = position_points_jitter(height = 0),
                      point_size = 1.5,
                      point_shape = 1,
                      alpha = 0.3) +
  coord_flip(xlim = c(-10, 40), ylim = NULL, expand = TRUE, clip = "on") +
  scale_color_manual(labels = "Median", values = "red", name= " ") +
  geom_point(aes(y = NUM_FEATURES, x = median_IR, color = "red"), shape = 15, data = median_plot) + # swapped xy bc of coord flip
  geom_line(aes(y = NUM_FEATURES, x = median_IR, color = "red"), shape = 15, data = median_plot) + # swapped xy bc of coord flip
  labs(y = "Number of Features", x = "Irreducible Error") + # swapped xy bc of coord flip 
  theme_bw() +
  theme(legend.position="bottom") +
  theme(axis.text = element_text(size = 8)) +
  theme(axis.title = element_text(size = 12)) +
  theme(legend.text = element_text(size = 12)) + 
  theme(legend.title = element_text(size = 12)) +
  facet_wrap(~factor_for_facet, nrow = 2)


#7.06
ggsave(filename=paste("LTP_final", "IR_ACS_wages.png", sep = "/"), width=4.36, height=4.36)


## by variable, take median of irreducible error 

variables_to_pivot <- c("educ", "empstat", "age", "sex", "fertyr", "marst", "uhrswork", "metro", "gq", "nfams", "sei", "vetstat", "trantime")

variable_plot <- results_from_ACS %>%
  pivot_longer(cols = variables_to_pivot, names_to = "variable", values_to = "included") %>%
  filter(included == 1) 

median_plot_by_variable <- variable_plot %>%
  group_by(variable, factor_for_facet) %>% 
  summarize(median_IR = median(IRREDUCIBLE_ERROR)) %>%
  group_by(variable)

ggplot(variable_plot, aes(x = IRREDUCIBLE_ERROR, y = as.factor(variable))) +
  geom_density_ridges(jittered_points = F,
                      position = position_points_jitter(height = 0),
                      point_size = 1.5,
                      point_shape = 1,
                      alpha = 0.3) +
  coord_flip(xlim = c(-10, 40), ylim = NULL, expand = TRUE, clip = "on") +
  labs(y = "Features", x = "Irreducible Error") + # swapped xy bc of coord flip 
  theme_bw() +
  scale_color_manual(labels = "Median", values = "red", name= " ") +
  geom_point(aes(y = variable, x = median_IR, color = "red"), shape = 15, data = median_plot_by_variable) + # swapped xy bc of coord flip
  theme(legend.position="bottom") +
  theme(axis.text = element_text(size = 8)) +
  theme(axis.title = element_text(size = 12)) +
  theme(legend.text = element_text(size = 12)) + 
  theme(legend.title = element_text(size = 12)) +
  facet_wrap(~resolution, nrow = 2) +
  theme(axis.text.x = element_text(angle = 90, hjust = 1))
  
ggsave(filename=paste("LTP_final", "IR_ACS_wages_by_variable.png", sep = "/"), width=4.36, height=4.36)

ACS_data <- read_csv(paste("LTP_final", "ACS_clean_LTP_final.csv", sep = "/")) 

## summary statistics 

variables_to_summarize <- c("educ", "empstat", "age", "sex", "fertyr", "marst", "uhrswork", "metro", "gq", "nfams", "sei", "vetstat", "trantime")

ACS_summary <- ACS_data %>%
  pivot_longer(cols = variables_to_summarize, names_to = "variable", values_to = "value") %>%
  group_by(variable) %>%
  summarize(mean = mean(value, na.rm=T),
            sd = sd(value, na.rm=T))  


latex_table <- ACS_summary %>%
  kable(format = "latex", digits=2) %>%
  kable_styling()


ACS_data_for_figure <- ACS_data %>%
  mutate(log_income_clean = log(income_clean + 1)) %>%
  select(income_clean, log_income_clean)


ACS_long <- ACS_data_for_figure %>%
  pivot_longer(cols = c("income_clean", "log_income_clean"), names_to = "variable", values_to = "value") %>%
  mutate(value = ifelse(variable == "income_clean", value/1000, value))  # transforming income_clean for histogram 



## histograms 

ggplot(ACS_long, aes(x = value)) +
  geom_histogram() +
  facet_wrap(~variable, scales = "free",
             labeller = labeller(variable = c("income_clean" = "Raw Income", "log_income_clean" = "Transformed Income"))) +
  theme_bw() +
  labs(y = "Frequency", x = "Income Measure (Raw Income in '000s)") +
  theme(axis.text = element_text(size = 12)) +
  theme(axis.title = element_text(size = 12)) +
  theme(legend.text = element_text(size = 12)) + 
  theme(legend.title = element_text(size = 12))
  
ggsave(filename=paste("LTP_final", "wage_histograms.png", sep = "/"), width=7.06, height=4.36)

