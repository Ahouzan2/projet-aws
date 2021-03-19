import csv
import logging
import logging.handlers
import os
import re
from datetime import datetime

import boto3
import botocore.exceptions


ACCESS_KEY = "AKIA5PBERXB2QBB2SCWN"
SECRET_KEY = "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"


logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")
logger = logging.getLogger(__name__)  # Logging handler for log file


def config_logger():
    """

    """
    global logger
    directory = os.path.dirname(__file__)
    os.chdir(directory)
    logfile = directory + "/log"

    if not os.path.exists(logfile):
        os.makedirs(logfile)

    nameofscript = (str(__file__).split("/")[-1]).split(".")[0]

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(logfile + "/" + nameofscript + ".log")

    # Create formatters and add it to handlers
    c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)


def volume_exists(volume_id, volumes):
    """

    :param volume_id:
    :param volumes:
    :return:
    """
    return volume_id in volumes if volume_id else ""


def instance_exists(instance_id, instances):
    """

    :param instance_id:
    :param instances:
    :return:
    """
    return instance_id in instances if instance_id else ""


def image_exists(image_id, images):
    """

    :param image_id:
    :param images:
    :return:
    """
    return image_id in images if image_id else ""


def get_snapshots(ec2):
    """

    :param ec2:
    :return:
    """
    snapshots_dict = []
    try:
        snapshots_desc = ec2.describe_snapshots(OwnerIds=["self"])
    except botocore.exceptions.ClientError as error:
        logger.error("main: can t get snapshot describe ")
        logger.error("message error: %s" % error)
        return None
    while True:

        for v in snapshots_desc["Snapshots"]:
            snapshots_dict.append(v)
        if "NextToken" not in snapshots_desc:
            break
        try:
            snapshots_desc = ec2.describe_snapshots(
                NextToken=snapshots_desc["NextToken"]
            )
        except botocore.exceptions.ClientError as error:
            logger.error("main: can t get snapshot describe ")
            logger.error("message error: %s" % error)
            return None
    return snapshots_dict


def get_volumes(ec2):
    """

    :param ec2:
    :return:
    """
    volumes_dict = {}
    try:
        volumes_desc = ec2.describe_volumes()
    except botocore.exceptions.ClientError as error:
        logger.error("main: can tget volumes describe ")
        logger.error("message error: %s" % error)
        return None
    while True:
        for v in volumes_desc["Volumes"]:
            volumes_dict[v["VolumeId"]] = v
        if "NextToken" in volumes_desc:
            volumes_desc = ec2.describe_volumes(NextToken=volumes_desc["NextToken"])
        else:
            break
    return volumes_dict


def get_instances(ec2):
    """

    :param ec2:
    :return:
    """
    try:
        reservations = ec2.describe_instances()["Reservations"]
    except botocore.exceptions.ClientError as error:
        logger.error("main: can t collect instances reservations list ")
        logger.error("message error: %s" % error)
        return None

    instances = [
        instance
        for reservation in reservations
        for instance in reservation["Instances"]
    ]
    return dict([(i["InstanceId"], i) for i in instances])


def get_images(ec2):
    """

    :param ec2:
    :return:
    """
    try:
        images = ec2.describe_images(Owners=["self"])["Images"]
    except botocore.exceptions.ClientError as error:
        logger.error("main: can t collect image list ")
        logger.error("message error: %s" % error)
        return None

    return dict([(i["ImageId"], i) for i in images])


def parse_description(description):
    """

    :param description:
    :return:
    """
    regex = r"^Created by CreateImage\((.*?)\) for (.*?) "

    matches = re.finditer(regex, description, re.MULTILINE)
    for matchNum, match in enumerate(matches):
        return match.groups()
    return "", ""


def main():
    """

    """
    config_logger()
    default_region = "eu-west-1"
    try:

        ec2 = boto3.client(
            "ec2",
            region_name=default_region,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
        )
    except botocore.exceptions.ClientError as error:
        logger.error("main: can t connect with credentials ")
        logger.error("message error: %s" % error)
        exit(1)

    try:
        response = ec2.describe_regions()
    except botocore.exceptions.ClientError as error:
        logger.error("main: can t get regions list  ")
        logger.error("message error: %s" % error)
        exit(1)

    for region in response["Regions"]:
        logger.debug(region)
        work_region = region["RegionName"]
        try:
            ec2 = boto3.client(
                "ec2",
                region_name=work_region,
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY,
            )
        except botocore.exceptions.ClientError as error:
            logger.error("main: can t connect to regions: %s " % work_region)
            logger.error("message error: %s" % error)
            continue
        try:
            logger.info("get volumes for regions:%s" % work_region)
            volumes = get_volumes(ec2)
            if volumes is None:
                logger.warning(
                    " no volumes list for region with exception %s" % work_region
                )
                continue

            logger.info("get instances for regions:%s" % work_region)
            instances = get_instances(ec2)
            if instances is None:
                logger.warning(
                    " no instances list for region %s with exceptions" % work_region
                )
                continue
            logger.info("get instances for regions:%s" % work_region)
            images = get_images(ec2)
            if images is None:
                logger.warning(
                    " no images list for region %s with exceptions" % work_region
                )
                continue

        except botocore.exceptions.ClientError as error:
            logger.error("main: can t get instances volumes iamges list  ")
            logger.error("message error: %s" % error)
            continue
        file_name = (
            "report_"
            + work_region
            + "_"
            + (datetime.now()).strftime("%Y%m%d-%H%M%S")
            + ".csv"
        )
        logger.info("build file for region:%s" % work_region)
        with open(file_name, "a+") as csvfile:
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
            try:
                list_snapshots = get_snapshots(ec2)
                if list_snapshots is None:
                    logger.warning("no snapshot list for region %s" % work_region)
                    continue
            except botocore.exceptions.ClientError as error:
                logger.error("main: can t get snpashot list   ")
                logger.error("message error: %s" % error)
                continue

            for snap in list_snapshots:
                try:
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
                except Exception as error:
                    logger.warning(" can t build file csv recodr for %s" % snap)
                    logger.warning("message error:%s" % error)
            logger.info("end build file for region:%s" % work_region)


if __name__ == "__main__":
    main()
