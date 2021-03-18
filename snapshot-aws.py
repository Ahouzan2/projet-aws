import re
import boto3
import csv
from botocore.exceptions import ClientError
import logging

from datetime import datetime

global REGION
REGION = "eu-west-1"


def volume_exists(volume_id, volumes):
    return volume_id in volumes if volume_id else ""


def instance_exists(instance_id, instances):
    return instance_id in instances if instance_id else ""


def image_exists(image_id, images):
    return image_id in images if image_id else ""


def get_snapshots(ec2):
    return ec2.describe_snapshots(OwnerIds=["self"])["Snapshots"]


def get_volumes(ec2):
    return dict([(v["VolumeId"], v) for v in ec2.describe_volumes()["Volumes"]])


def get_instances(ec2):
    reservations = ec2.describe_instances()["Reservations"]

    instances = [
        instance
        for reservation in reservations
        for instance in reservation["Instances"]
    ]
    return dict([(i["InstanceId"], i) for i in instances])


def get_images(ec2):
    images = ec2.describe_images(Owners=["self"])["Images"]

    return dict([(i["ImageId"], i) for i in images])


def parse_description(description):
    regex = r"^Created by CreateImage\((.*?)\) for (.*?) "

    matches = re.finditer(regex, description, re.MULTILINE)
    for matchNum, match in enumerate(matches):
        return match.groups()
    return "", ""


def main():
    ec2 = boto3.client("ec2", region_name=REGION,)

    # ec2_client = boto3.client('ec2')
    response = ec2.describe_regions()
    for region in response["Regions"]:
        print(region)
        work_region = region["RegionName"]
        ec2 = boto3.client("ec2", region_name=work_region)

        volumes = get_volumes(ec2)
        instances = get_instances(ec2)
        images = get_images(ec2)
        myfile_name = (
            "report_"
            + work_region
            + "_"
            + (datetime.now()).strftime("%Y%m%d-%H%M%S")
            + ".csv"
        )
        with open(myfile_name, "a+") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "snapshot id",
                    "description",
                    "started",
                    "size",
                    "volume",
                    "volume exists",
                    "instance",
                    "instance exists",
                    "ami",
                    "ami exists",
                ]
            )
            for snap in get_snapshots(ec2):
                instance_id, image_id = parse_description(snap["Description"])
                writer.writerow(
                    [
                        snap["SnapshotId"],
                        snap["Description"],
                        snap["StartTime"],
                        str(snap["VolumeSize"]),
                        snap["VolumeId"],
                        str(volume_exists(snap["VolumeId"], volumes)),
                        instance_id,
                        str(instance_exists(instance_id, instances)),
                        image_id,
                        str(image_exists(image_id, images)),
                    ]
                )


if __name__ == "__main__":
    main()
