library(shiny)
library(ggplot2)
library(dplyr)
library(lubridate)
library(plotly)
library(DT)
library(data.table)  # For faster data reading and processing
library(shinyWidgets)  # For progress bar

options(shiny.maxRequestSize = 100 * 1024^2)

# Define UI
ui <- fluidPage(
  titlePanel("Usage Count Analysis"),
  
  sidebarLayout(
    sidebarPanel(
      fileInput("file", "Upload CSV File", accept = ".csv"),
      selectInput(
        "timePeriod", 
        "Select Time Period:", 
        choices = c("By Day" = "day", "By Week" = "week", "By Month" = "month"),
        selected = "day"
      ),
      dateRangeInput("dateRange", "Select Date Range:",
                     start = Sys.Date() - 30, 
                     end = Sys.Date()),
      numericInput("hline", "Horizontal Line (Default = 0):", value = 0, step = 1),
      sliderInput("yAxisRange", "Adjust Y-Axis Range:",
                  min = 0, max = 50000, value = c(0, 10000)),  # Set slider range to 0-50,000
      actionButton("refresh", "Refresh"),
      downloadButton("exportDetails", "Export Detailed Dataset"),
      downloadButton("exportAggregated", "Export Aggregated Counts")
    ),
    
    mainPanel(
      tabsetPanel(
        tabPanel("Usage Over Time",
                 plotlyOutput("lineChart"),
                 br(),
                 DTOutput("dataTable")
        )
      )
    )
  )
)

# Define Server Logic
server <- function(input, output, session) {
  
  # Reactive dataset from uploaded file
  dataset <- reactive({
    req(input$file)
    
    # Show progress bar during file upload
    progress <- Progress$new(session)
    progress$set(message = "Loading file...", value = 0)
    
    # Use fread for efficient reading
    data <- tryCatch({
      data.table::fread(input$file$datapath, stringsAsFactors = FALSE)
    }, error = function(e) {
      showNotification("Error reading file. Please check the file format.", type = "error")
      return(NULL)
    })
    
    # Validate the 'timestamp' column
    if (!("timestamp" %in% names(data))) {
      stop("The uploaded file must contain a 'timestamp' column.")
    }
    
    # Convert timestamp to POSIXct
    data[, timestamp := as.POSIXct(timestamp, format = "%Y-%m-%dT%H:%M:%OS", tz = "Asia/Singapore")]
    
    # Clean up memory
    gc()
    progress$close()
    data
  })
  
  # Reactive data based on date range and time period
  filteredData <- reactive({
    req(dataset())
    data <- dataset()
    
    # Filter by date range
    data <- data[timestamp >= input$dateRange[1] & timestamp <= input$dateRange[2]]
    
    if (nrow(data) == 0) {
      return(NULL)  # Return NULL if no data is in the selected date range
    }
    
    # Group by time period
    timePeriod <- input$timePeriod
    data[, period := switch(
      timePeriod,
      day = as.Date(timestamp),
      week = floor_date(timestamp, "week"),
      month = floor_date(timestamp, "month")
    )]
    data <- data[, .(count = .N), by = period]
    data
  })
  
  # Reactive data for the table
  tableData <- reactive({
    req(filteredData())
    data <- filteredData()
    
    timePeriod <- input$timePeriod
    if (timePeriod == "month") {
      data[, `:=`(
        Year = year(period),
        Month = format(period, "%b %Y"),  # Format month as "Jan 2022"
        `Date Range` = paste0(format(period, "%Y-%m-01"), " to ", format(period + months(1) - days(1), "%Y-%m-%d"))
      )]
      data <- data[, .(Year, Month, `Date Range`, count)]
    } else if (timePeriod == "week") {
      data[, `Date and Year Range` := paste0(format(period, "%Y-%m-%d"), " to ", format(period + weeks(1) - days(1), "%Y-%m-%d"))]
      data <- data[, .(`Date and Year Range`, count)]
    } else if (timePeriod == "day") {
      data[, `Date and Year Range` := as.character(period)]
      data <- data[, .(`Date and Year Range`, count)]
    }
    data
  })
  
  # Render the line chart
  output$lineChart <- renderPlotly({
    req(filteredData())
    data <- filteredData()
    
    if (is.null(data) || nrow(data) == 0) {
      showNotification("No data available for the selected range.", type = "warning")
      return(NULL)
    }
    
    # Generate the base plot
    p <- ggplot(data, aes(x = period, y = count)) +
      geom_line() +
      geom_point() +
      labs(
        title = "Usage Over Time",
        x = "Time Period",
        y = "Number of Counts"
      ) +
      theme_minimal()
    
    # Add horizontal line if input provided, default to 0
    p <- p + geom_hline(yintercept = input$hline, color = "red", linetype = "dashed")
    
    # Adjust Y-axis range dynamically
    p <- p + coord_cartesian(ylim = input$yAxisRange)
    
    ggplotly(p)
  })
  
  # Render the data table
  output$dataTable <- renderDT({
    req(tableData())
    datatable(
      tableData(),
      options = list(pageLength = 10, order = list(0, 'asc')),
      rownames = FALSE
    )
  })
  
  # Export detailed dataset
  output$exportDetails <- downloadHandler(
    filename = function() { paste("Detailed_Dataset_", Sys.Date(), ".csv", sep = "") },
    content = function(file) {
      req(dataset())
      data <- dataset()
      
      # Add additional columns to the detailed dataset
      data[, `:=`(
        day_of_week = format(timestamp, "%a"),  # Day of the week
        time = format(timestamp, "%H:%M:%S"),  # Time of day
        week_period = paste0(
          format(floor_date(timestamp, "week"), "%Y-%m-%d"), 
          " to ", 
          format(floor_date(timestamp, "week") + weeks(1) - days(1), "%Y-%m-%d")
        )  # Week period
      )]
      fwrite(data, file)
    }
  )
  
  # Export aggregated counts
  output$exportAggregated <- downloadHandler(
    filename = function() { paste("Aggregated_Counts_", Sys.Date(), ".csv", sep = "") },
    content = function(file) {
      req(tableData())
      agg_data <- tableData()
      fwrite(agg_data, file)
    }
  )
}

# Run the app
shinyApp(ui, server)














