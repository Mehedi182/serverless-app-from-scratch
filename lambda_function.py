import json
import logging

import boto3

from custom_encoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table = "employee"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table)

employee_path = "/employee"


def buildResponse(statusCode, body=None):
    response = {
        "statusCode": statusCode,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
    if body is not None:
        response["body"] = json.dumps(body, cls=CustomEncoder)
    return response


def get_employees():
    try:
        # Use the scan method to retrieve all items from the table
        response = table.scan()

        # Extract the items from the response
        items = response.get("Items", [])

        # Return the items as a JSON response
        return {"statusCode": 200, "body": json.dumps(items)}
    except Exception:
        logger.exception("Cannot Fetch Employees")

        return {"statusCode": 500, "body": json.dumps({"error": "Error fetching data"})}


def get_employee(id):
    try:
        response = table.get_item(Key={"PK": id})

        item = response.get("Item")

        if item:
            return {"statusCode": 200, "body": json.dumps(item)}
        else:
            return {"statusCode": 404, "body": json.dumps({"error": "Item not found"})}
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"error": "Error fetching data"})}


def create_employee(item):
    try:
        item = {
            "PK": item["phone"],
            "name": item["name"],
            "phone": item["phone"],
            "email": item["email"],
            "age": item["age"],
        }
        table.put_item(Item=item)
        body = {"Message": "Success", "Item": item}

        return buildResponse(200, body)
    except Exception:
        logger.exception("Cannot Create the Employee")


def update_employee(event):
    try:
        request_body = json.loads(event["body"])

        response = table.update_item(
            Key={"PK": event["pathParameters"]["id"]},
            UpdateExpression="""SET 
            #name = :name,
            #phone = :phone,
            #email = :email,
            #age = :age
            """,
            ExpressionAttributeNames={
                "#name": "name",
                "#phone": "phone",
                "#email": "email",
                "#age": "age",
            },
            ExpressionAttributeValues={
                ":name": request_body["name"],
                ":phone": request_body["phone"],
                ":email": request_body["email"],
                ":age": request_body["age"],
            },
            ReturnValues="ALL_NEW",
        )

        # Extract the updated item from the response
        updated_item = response.get("Attributes")

        return {"statusCode": 200, "body": json.dumps(updated_item)}
    except Exception:
        logger.exception("Cannot Update")
        return {"statusCode": 500, "body": json.dumps({"error": "Error updating data"})}


def delete_employee(id):
    try:
        response = table.delete_item(Key={"PK": id})
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            return {"statusCode": 204}
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Error deleting data"}),
            }
    except Exception:
        logger.exception("Cannot Delete the Employee")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal Server Error"}),
        }


def lambda_handler(event, context):
    logger.info(event)
    print(event["resource"])
    httpMethod = event["httpMethod"]
    path = event["path"]

    if httpMethod == "GET" and path == employee_path:
        response = get_employees()

    elif httpMethod == "POST" and path == employee_path:
        response = create_employee(json.loads(event["body"]))
    elif event["resource"] == "/employee/{id}":
        if httpMethod == "GET":
            response = get_employee(event["pathParameters"]["id"])
        elif httpMethod == "PUT":
            response = update_employee(event)
        elif httpMethod == "DELETE":
            response = delete_employee(event["pathParameters"]["id"])

    return response

