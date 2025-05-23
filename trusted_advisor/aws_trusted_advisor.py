#!/usr/bin/env python3
import boto3
import csv
import os
import datetime
import matplotlib.pyplot as plt


def get_cost_savings_data():
    """
    Retrieves cost optimization check results from Trusted Advisor.
    For each check in the 'cost_optimizing' category, the function attempts
    to find a column that includes savings information (e.g. "Estimated Monthly Savings")
    and sums up the values while also counting the number of flagged resources.
    """
    client = boto3.client("support")
    response = client.describe_trusted_advisor_checks(language="en")
    total_savings = 0.0
    total_opportunities = 0

    for check in response.get("checks", []):
        if check.get("category") == "cost_optimizing":
            check_id = check.get("id")
            try:
                result_response = client.describe_trusted_advisor_check_result(
                    checkId=check_id, language="en"
                )
            except Exception:
                continue  # Skip this check if there is an error retrieving its result

            result = result_response.get("result", {})
            metadata_headers = result.get("metadata", [])
            flagged_resources = result.get("flaggedResources", [])

            # Identify the index of the column that likely contains savings info.
            savings_index = None
            for i, header in enumerate(metadata_headers):
                if "Savings" in header:
                    savings_index = i
                    break

            if savings_index is not None:
                for resource in flagged_resources:
                    try:
                        # Remove currency symbols and commas then convert to float.
                        savings_str = resource[savings_index]
                        savings_value = float(
                            savings_str.replace("$", "").replace(",", "").strip()
                        )
                        total_savings += savings_value
                    except Exception:
                        pass

            total_opportunities += len(flagged_resources)
    return total_savings, total_opportunities


def update_csv(csv_filename, month_str, total_savings, total_opportunities):
    """
    Updates the CSV file with the data for the current month.
    If an entry for the current month already exists, it is updated;
    otherwise, a new record is appended.
    """
    rows = []
    header = ["Month", "TotalSavings", "TotalOpportunities"]

    if os.path.exists(csv_filename):
        with open(csv_filename, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append(row)

    # Update existing record for the month if found.
    updated = False
    for row in rows:
        if row["Month"] == month_str:
            row["TotalSavings"] = str(total_savings)
            row["TotalOpportunities"] = str(total_opportunities)
            updated = True
            break

    if not updated:
        rows.append(
            {
                "Month": month_str,
                "TotalSavings": str(total_savings),
                "TotalOpportunities": str(total_opportunities),
            }
        )

    # Write sorted data back to the CSV.
    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        for row in sorted(rows, key=lambda x: x["Month"]):
            writer.writerow(row)


def plot_data(csv_filename, output_filename):
    """
    Reads the CSV file and plots the monthly total savings and opportunities.
    The graph uses a dual-axis layout to display both metrics.
    """
    months = []
    savings = []
    opportunities = []
    with open(csv_filename, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            months.append(row["Month"])
            savings.append(float(row["TotalSavings"]))
            opportunities.append(int(row["TotalOpportunities"]))

    fig, ax1 = plt.subplots()
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Total Savings ($)", color="tab:blue")
    ax1.plot(months, savings, marker="o", color="tab:blue", label="Total Savings ($)")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    plt.xticks(rotation=45)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Total Opportunities", color="tab:red")
    ax2.plot(
        months, opportunities, marker="s", color="tab:red", label="Total Opportunities"
    )
    ax2.tick_params(axis="y", labelcolor="tab:red")

    plt.title("AWS Trusted Advisor Cost Savings & Opportunities")
    fig.tight_layout()
    plt.savefig(output_filename)
    plt.close()


def main():
    total_savings, total_opportunities = get_cost_savings_data()
    now = datetime.datetime.now()
    month_str = now.strftime("%Y-%m")
    csv_filename = "ta_cost_savings.csv"
    update_csv(csv_filename, month_str, total_savings, total_opportunities)
    output_filename = "ta_cost_savings.png"
    plot_data(csv_filename, output_filename)
    print(
        "Data for month {}: Savings = ${}, Opportunities = {}".format(
            month_str, total_savings, total_opportunities
        )
    )
    print(
        "CSV data updated in '{}' and graph saved as '{}'.".format(
            csv_filename, output_filename
        )
    )


if __name__ == "__main__":
    main()
