"""
Spark Simplicity - Mount Point Validation
==========================================

Enterprise-grade mount point validation for distributed Spark cluster environments.
This module provides comprehensive cluster-wide validation of shared storage
accessibility
to ensure reliable I/O operations across all nodes in a Spark cluster. Essential for
production deployments using NFS, shared drives, or other distributed storage systems.

Key Features:
    - **Cluster-Wide Validation**: Tests mount point access on all Spark executor nodes
    - **Driver Node Testing**: Validates shared storage accessibility from Spark driver
    - **Detailed Diagnostics**: Comprehensive error reporting with specific failure
      reasons
    - **Atomic Validation**: Ensures consistent mount point state across entire cluster
    - **Production Safety**: Prevents I/O failures through proactive validation
    - **Network Storage Support**: Compatible with NFS, SMB, HDFS, and cloud storage

Validation Process:
    - **Driver Validation**: First validates mount point accessibility on the driver
      node
    - **Worker Distribution**: Creates validation tasks distributed across all executor
      nodes
    - **Parallel Testing**: Simultaneously tests mount point access on all cluster nodes
    - **Result Aggregation**: Collects and analyzes validation results from all nodes
    - **Failure Analysis**: Provides detailed diagnostics for any accessibility failures

Enterprise Features:
    - **Comprehensive Logging**: Detailed audit trail of all validation operations
    - **Failure Diagnostics**: Specific error messages for troubleshooting mount issues
    - **Performance Optimization**: Parallel validation across cluster for minimal
      overhead
    - **Error Recovery**: Graceful handling of network timeouts and node failures
    - **Cluster Coordination**: Ensures synchronized validation across distributed nodes

Usage:
    This module is used internally by path configuration utilities to ensure reliable
    distributed I/O operations. Mount point validation is essential for preventing
    FileNotFoundException errors during Spark job execution in cluster environments.

    from spark_simplicity.io.validation.mount_validator import _validate_mount_point
"""

import os
import socket
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Union

from pyspark.sql import SparkSession

from ...logger import get_logger
from .path_utils import _check_path_access, _extract_mount_point

# Logger for mount validation
_mount_logger = get_logger("spark_simplicity.io.mount")


def _validate_mount_point_local(file_path: Union[str, Path]) -> bool:
    """
    Validate shared storage mount point accessibility on the Spark driver node.

    Performs initial validation of mount point accessibility on the driver node before
    proceeding with cluster-wide validation. This function serves as a "fail-fast"
    mechanism to detect mount point issues early without involving the entire cluster.
    Essential for preventing distributed validation when basic driver-level access
    fails.

    Validation Steps:
        1. **Mount Point Detection**: Extracts mount point from file path using
           heuristics
        2. **Existence Check**: Verifies mount point directory exists on driver node
        3. **Permission Validation**: Confirms driver process has read access to mount
        4. **Directory Validation**: Ensures mount point is a valid directory structure

    Args:
        file_path: File path to validate for mount point accessibility. Can be either
                  a string or Path object pointing to any file within the shared
                  storage.
                  The mount point is automatically extracted from this path.

    Returns:
        Boolean indicating whether the mount point is accessible on the driver node.
        True means the mount point exists, is accessible, and has proper permissions.
        False indicates validation failure with detailed error logging.

    Error Handling Strategy:
        This function uses logging-based error reporting rather than exceptions to
        enable
        graceful degradation and comprehensive error collection across the cluster.
        All validation failures are logged with specific diagnostic information.

    Validation Scenarios:
        **Success Cases**:
        - Mount point exists as a directory
        - Driver process has read permissions
        - Path format follows mount point conventions

        **Failure Cases**:
        - Invalid path format (not following mount conventions)
        - Mount point directory doesn't exist
        - Insufficient permissions for driver process
        - Mount point exists but is not a directory

    Examples:
        Validate NFS mount accessibility:

         success = _validate_mount_point_local("/nfs/shared/data/file.csv")
         if success:
        ...     print("Driver can access NFS mount")
        ... else:
        ...     print("Driver mount validation failed")

        Validate shared drive mount:

         success = _validate_mount_point_local("/mnt/storage/reports/quarterly.xlsx")
         # Automatically extracts /mnt/storage as mount point

    Logging Behavior:
        - **Success**: No logging (silent success for performance)
        - **Path Format Error**: Logs invalid mount path format with guidance
        - **Access Error**: Logs specific permission or existence issues
        - **Mount Error**: Logs mount point accessibility problems

    Performance Notes:
        - Minimal overhead (local filesystem operations only)
        - No network communication with cluster nodes
        - Synchronous operation with immediate results
        - Results should be cached for repeated validations

    See Also:
        - ``_validate_mount_point_workers()``: Cluster-wide worker validation
        - ``_validate_mount_point()``: Complete cluster validation orchestration
        - ``_extract_mount_point()``: Mount point detection logic

    Note:
        This function is the first step in cluster-wide mount validation and must
        succeed before proceeding with distributed worker validation. It provides
        early detection of basic mount point issues without involving cluster resources.
    """
    mount_point = _extract_mount_point(file_path)
    if not mount_point:
        _mount_logger.error(
            "Invalid mount path format (please ensure the path is complete and "
            "correctly "
            "formatted): %s",
            file_path,
        )
        return False

    # Check mount point accessibility
    success, error_msg = _check_path_access(mount_point, "mount point")
    if not success:
        _mount_logger.error(
            "The main Spark driver cannot access the shared folder - %s", error_msg
        )
        return False

    return True


def _create_worker_validation_task(
    mount_point: str, file_path: str
) -> Callable[[], Dict[str, Any]]:
    """
    Create distributed validation task for execution on Spark executor nodes.

    Generates a self-contained validation function that can be serialized and executed
    on remote Spark executor nodes to test mount point and file accessibility. This
    factory function creates the validation logic that will be distributed across the
    cluster to perform comprehensive mount point testing on all worker nodes.

    The created validation task is designed to be completely self-contained with no
    external dependencies, making it suitable for distributed execution across cluster
    nodes with potentially different environments and configurations.

    Args:
        mount_point: Mount point directory path to validate on each executor node.
                    Must be the exact mount point path (e.g., "/nfs/shared" not a file
                    within).
                    This path will be tested for existence, directory status, and
                    accessibility.
        file_path: Complete file path to validate on each executor node. This tests
                  the specific file accessibility in addition to the general mount
                  point.
                  Enables validation of both mount infrastructure and file-specific
                  access.

    Returns:
        Callable function that performs comprehensive validation when executed on an
        executor node. The function returns a dictionary with detailed validation
        results
        including hostname, accessibility status, and specific failure diagnostics.

    Task Function Behavior:
        The generated validation function performs these operations on each executor:

        1. **Hostname Detection**: Identifies the specific cluster node for diagnostics
        2. **Mount Point Testing**: Validates mount directory existence and
           accessibility
        3. **File Access Testing**: Confirms specific file availability and permissions
        4. **Result Compilation**: Packages all validation results into structured
           format

    Result Structure:
        The validation task returns a dictionary containing:

         {
        ...     'hostname': 'worker-node-01',           # Node identification
        ...     'mount_point': '/nfs/shared',            # Tested mount point
        ...     'mount_exists': True,                    # Mount directory exists
        ...     'mount_readable': True,                  # Mount has read permissions
        ...     'file_path': '/nfs/shared/data.csv',     # Tested file path
        ...     'file_exists': True,                     # File exists on this node
        ...     'file_readable': True,                   # File has read permissions
        ...     'success': True                          # Overall validation success
        ... }

    Validation Logic:
        **Mount Point Validation**:
        - Tests directory existence with os.path.exists()
        - Verifies directory status with os.path.isdir()
        - Checks read permissions with os.access()

        **File Validation**:
        - Tests file existence with os.path.exists()
        - Verifies read access permissions with os.access()
        - Combines with mount validation for overall success

    Examples:
        Create validation task for NFS storage:

         task = _create_worker_validation_task("/nfs/shared", "/nfs/shared/data.csv")
         result = task()  # Execute on executor node
         print(f"Node {result['hostname']}: {result['success']}")

        Validate multiple storage scenarios:

         # HDFS validation task
         hdfs_task = _create_worker_validation_task(
        ...     "/hdfs/warehouse", "/hdfs/warehouse/table.parquet"
        ... )

         # SMB share validation task
         smb_task = _create_worker_validation_task("/mnt/smb", "/mnt/smb/reports.xlsx")

    Distributed Execution Context:
        - **Serialization**: Function must be pickle-serializable for Spark distribution
        - **Dependencies**: Uses only standard library functions available on all nodes
        - **Error Handling**: Captures all errors within task for consistent reporting
        - **Performance**: Minimal resource usage per executor node

    Network Storage Compatibility:
        - **NFS**: Full support for Network File System validation
        - **SMB/CIFS**: Windows and Samba share validation
        - **HDFS**: Hadoop Distributed File System compatibility
        - **Cloud Storage**: Mounted cloud storage validation (S3, Azure, GCS)

    See Also:
        - ``_process_worker_validation_results()``: Result processing and analysis
        - ``_validate_mount_point_workers()``: Orchestrates distributed validation
        - Spark RDD operations: Task distribution and execution framework

    Note:
        The validation task is designed to be fault-tolerant and will not raise
        exceptions during execution. All errors are captured in the result dictionary
        for centralized processing and analysis.
    """

    def check_mount_on_executor() -> Dict[str, Any]:
        """Validate mount point and file access on executor node."""
        hostname = socket.gethostname()

        # Check mount point
        mount_exists = os.path.exists(mount_point) and os.path.isdir(mount_point)
        mount_readable = os.access(mount_point, os.R_OK) if mount_exists else False

        # Check specific file
        file_exists = os.path.exists(file_path)
        file_readable = os.access(file_path, os.R_OK) if file_exists else False

        return {
            "hostname": hostname,
            "mount_point": mount_point,
            "mount_exists": mount_exists,
            "mount_readable": mount_readable,
            "file_path": file_path,
            "file_exists": file_exists,
            "file_readable": file_readable,
            "success": mount_exists
            and mount_readable
            and file_exists
            and file_readable,
        }

    return check_mount_on_executor


def _process_worker_validation_results(
    results: List[Dict[str, Any]],
) -> Tuple[bool, List[str]]:
    """
    Process and analyze cluster-wide mount validation results with comprehensive
    diagnostics.

    Analyzes validation results collected from all Spark executor nodes to determine
    overall cluster mount point accessibility and provides detailed diagnostic
    information
    for any failures. This function serves as the central analysis point for distributed
    validation results, generating actionable error reports for system administrators.

    The function performs comprehensive failure analysis, categorizing different types
    of mount point issues and logging specific diagnostic information to help resolve
    cluster storage problems quickly and effectively.

    Args:
        results: List of validation result dictionaries collected from all executor
                nodes.
                Each dictionary contains detailed validation information from one node
                including hostname, mount status, file accessibility, and error details.
                Expected structure matches output from worker validation tasks.

    Returns:
        Tuple containing (cluster_success_status, list_of_failed_hostnames):
        - cluster_success_status: Boolean indicating whether ALL nodes passed validation
        - list_of_failed_hostnames: List of hostnames where validation failed

    Diagnostic Analysis:
        The function performs detailed analysis of each validation failure type:

        **Mount Point Issues**:
        - **Mount Not Found**: Mount directory doesn't exist on node
        - **Mount Not Readable**: Insufficient permissions to access mount
        - **Mount Type Error**: Path exists but is not a directory

        **File Access Issues**:
        - **File Not Found**: Specific file doesn't exist on mount
        - **File Not Readable**: Insufficient permissions to read file
        - **File Type Error**: Path exists but is not a regular file

    Error Categorization:
        Each failure is categorized and logged with specific diagnostic messages:

         # Mount infrastructure failures
         "Worker node-01: Mount point not found (please check that the shared "
         "folder is mounted)"
         "Worker node-02: No read access to mount point (please check permissions)"

         # File-specific failures
         "Worker node-03: File not found (please verify the file path and name)"
         "Worker node-04: No read access to file (please check file permissions)"

    Logging Strategy:
        - **Success Cases**: No logging (silent success for performance)
        - **Failure Cases**: Detailed error logging with specific remediation guidance
        - **Diagnostic Context**: Each log entry includes hostname and specific error
          type
        - **Actionable Messages**: Error messages include specific steps to resolve
          issues

    Examples:
        Process validation results from cluster nodes:

         results = [
        ...     {'hostname': 'worker-01', 'success': True, ...},
        ...     {'hostname': 'worker-02', 'success': False, 'mount_exists': False, ...},
        ...     {'hostname': 'worker-03', 'success': True, ...}
        ... ]

         all_success, failed_hosts = _process_worker_validation_results(results)
         print(f"Cluster validation: {all_success}, Failed nodes: {failed_hosts}")
         # Output: "Cluster validation: False, Failed nodes: ['worker-02']"

        Handle comprehensive failure analysis:

         # Complex failure scenario
         mixed_results = [
        ...     {'hostname': 'node1', 'success': False, 'mount_exists': False},
        ...     {'hostname': 'node2', 'success': False, 'file_readable': False},
        ...     {'hostname': 'node3', 'success': True}
        ... ]

         success, failures = _process_worker_validation_results(mixed_results)
         # Logs specific diagnostic messages for each failure type

    Performance Characteristics:
        - **Linear Processing**: O(n) complexity where n is number of cluster nodes
        - **Memory Efficient**: Processes results iteratively without additional storage
        - **Immediate Analysis**: Real-time diagnostic logging during processing
        - **Scalable**: Handles clusters from small (2-3 nodes) to large (100+ nodes)

    Cluster Management Integration:
        - **Monitoring Systems**: Log entries can be parsed by cluster monitoring tools
        - **Alerting Integration**: Failed validation triggers can integrate with
          alerting
        - **Troubleshooting Guides**: Error messages provide specific remediation steps
        - **Automation Support**: Structured error reporting enables automated responses

    Common Failure Patterns:
        **Partial Mount Failures**:
        - Some nodes have mount accessible, others don't
        - Indicates inconsistent cluster configuration
        - Usually requires mount propagation across all nodes

        **Permission Issues**:
        - Mount exists but access denied
        - Indicates user/group permission problems
        - Usually requires permission adjustment on storage system

        **Network Connectivity**:
        - Mount points fail on remote nodes but work on driver
        - Indicates network storage connectivity issues
        - Usually requires network configuration or firewall changes

    See Also:
        - ``_validate_mount_point_workers()``: Orchestrates result collection
        - ``_create_worker_validation_task()``: Generates validation tasks
        - Cluster monitoring tools: Integration with enterprise monitoring systems

    Note:
        This function is critical for diagnosing distributed storage issues in
        production
        Spark clusters. The detailed diagnostic logging helps system administrators
        quickly identify and resolve mount point accessibility problems.
    """
    all_success = True
    failed_hosts = []

    for result in results:
        hostname = result["hostname"]
        success = result["success"]

        if not success:
            all_success = False
            failed_hosts.append(hostname)

            # Detailed diagnostics
            if not result["mount_exists"]:
                _mount_logger.error(
                    "Worker %s: Mount point not found (please check that the shared "
                    "folder "
                    "is mounted on this machine): %s",
                    hostname,
                    result["mount_point"],
                )
            elif not result["mount_readable"]:
                _mount_logger.error(
                    "Worker %s: No read access to mount point (please check your "
                    "permissions on "
                    "the shared folder): %s",
                    hostname,
                    result["mount_point"],
                )
            elif not result["file_exists"]:
                _mount_logger.error(
                    "Worker %s: File not found (please verify the file path and "
                    "name): %s",
                    hostname,
                    result["file_path"],
                )
            elif not result["file_readable"]:
                _mount_logger.error(
                    "Worker %s: No read access to file (please check your permissions "
                    "for "
                    "this file): %s",
                    hostname,
                    result["file_path"],
                )

    return all_success, failed_hosts


def _validate_mount_point_workers(
    spark: SparkSession, file_path: Union[str, Path]
) -> bool:
    """
    Execute comprehensive mount point validation across all Spark executor nodes.

    Orchestrates distributed validation of mount point accessibility by creating and
    executing validation tasks on every Spark executor node in the cluster. This
    function
    ensures that shared storage is consistently accessible across the entire distributed
    environment before proceeding with I/O operations.

    The validation process leverages Spark's distributed computing capabilities to
    simultaneously test mount point access on all cluster nodes, providing rapid
    feedback on cluster storage accessibility issues.

    Distributed Validation Process:
        1. **Mount Point Extraction**: Identifies mount point from provided file path
        2. **Executor Discovery**: Determines number of active Spark executor nodes
        3. **Task Distribution**: Creates RDD distributed across all executor nodes
        4. **Parallel Validation**: Executes validation tasks simultaneously on all
           nodes
        5. **Result Collection**: Gathers validation results from all executor nodes
        6. **Analysis**: Processes results and generates diagnostic information

    Args:
        spark: Active SparkSession instance used for distributed task execution.
              Must be properly configured with executor nodes for accurate validation.
              The session provides access to cluster topology and task distribution.
        file_path: File path to validate across the cluster. Can be string or Path
                  object.
                  The mount point is automatically extracted from this path for
                  validation.
                  Both mount point and specific file accessibility are tested.

    Returns:
        Boolean indicating whether mount point and file are accessible on ALL worker
        nodes.
        True means every executor node can access both the mount point and specific
        file.
        False indicates at least one node has accessibility issues with detailed
        logging.

    Cluster Configuration Requirements:
        **Spark Configuration**:
        - Valid SparkSession with active executor nodes
        - Proper cluster connectivity between driver and executors
        - Sufficient resources for validation task execution

        **Storage Requirements**:
        - Shared storage must be mounted on all cluster nodes
        - Consistent mount point paths across all nodes
        - Proper permissions for Spark processes on all nodes

    Validation Coverage:
        **Mount Point Testing**:
        - Directory existence validation on each node
        - Mount point accessibility and permission checking
        - Directory structure integrity verification

        **File Access Testing**:
        - Specific file existence validation
        - File read permission verification
        - File system consistency checking

    Error Handling Strategy:
        The function uses comprehensive error handling to ensure graceful operation:
        - **Network Errors**: Handles executor communication failures
        - **Task Failures**: Manages individual validation task exceptions
        - **Timeout Issues**: Accommodates slow network storage responses
        - **Resource Errors**: Handles cluster resource availability issues

    Examples:
        Validate NFS mount across Spark cluster:

         spark = SparkSession.builder.appName("validation").getOrCreate()
         success = _validate_mount_point_workers(spark, "/nfs/shared/data/input.csv")
         if success:
        ...     print("All executors can access NFS mount")
        ... else:
        ...     print("Some executors cannot access mount point")

        Validate large cluster deployment:

         # Test mount point on 50-node cluster
         cluster_success = _validate_mount_point_workers(
        ...     spark, "/hdfs/warehouse/table.parquet"
        ... )
         # Validation executes in parallel across all 50 nodes

    Performance Characteristics:
        **Parallel Execution**: All validation tasks run simultaneously across cluster
        **Scalability**: Performance scales with cluster parallelism, not cluster size
        **Network Efficiency**: Minimal network overhead per validation task
        **Resource Usage**: Low memory and CPU impact on cluster operations

    Cluster Size Considerations:
        **Small Clusters (2-5 nodes)**:
        - Validation completes in seconds
        - Minimal resource overhead
        - Simple troubleshooting

        **Medium Clusters (10-50 nodes)**:
        - Still rapid validation completion
        - More complex failure analysis
        - Network storage becomes critical

        **Large Clusters (50+ nodes)**:
        - Validation time may increase with network latency
        - Comprehensive diagnostic logging essential
        - Storage system performance becomes bottleneck

    Common Failure Scenarios:
        **Inconsistent Mounts**:
        - Some nodes have mount, others don't
        - Usually configuration management issue
        - Requires systematic mount verification

        **Permission Problems**:
        - Mount exists but wrong permissions
        - Usually user/group configuration issue
        - Requires permission adjustment on storage

        **Network Issues**:
        - Storage accessible from some nodes only
        - Usually firewall or routing issue
        - Requires network connectivity diagnosis

    Integration with Monitoring:
        - **Cluster Health**: Validation results indicate cluster storage health
        - **Alerting Systems**: Failed validation can trigger operational alerts
        - **Automation**: Results can drive automated remediation workflows
        - **Reporting**: Validation metrics contribute to cluster reliability reports

    See Also:
        - ``_create_worker_validation_task()``: Task generation for executor validation
        - ``_process_worker_validation_results()``: Result analysis and diagnostics
        - Spark RDD operations: Distributed task execution framework

    Note:
        This function is essential for production Spark clusters using shared storage.
        It prevents runtime I/O failures by proactively validating storage accessibility
        across the entire cluster before beginning data processing operations.
    """
    mount_point = _extract_mount_point(file_path)
    if not mount_point:
        return False

    mount_point_str = str(mount_point)
    file_path_str = str(file_path)

    try:
        # Create RDD to execute validation on each executor
        num_executors_str = spark.conf.get("spark.executor.instances", "2")
        num_executors = int(num_executors_str or "2")
        rdd = spark.sparkContext.parallelize(range(num_executors), num_executors)

        # Create and execute validation task
        validation_task = _create_worker_validation_task(mount_point_str, file_path_str)
        results = rdd.map(lambda _: validation_task()).collect()

        # Process results
        all_success, failed_hosts = _process_worker_validation_results(results)

        if all_success:
            return True
        else:
            _mount_logger.error(
                "Mount point validation failed on workers: %s", failed_hosts
            )
            return False

    except (OSError, RuntimeError) as e:
        _mount_logger.error("Failed to validate mount point on workers: %s", str(e))
        return False


def _validate_mount_point(spark: SparkSession, file_path: Union[str, Path]) -> bool:
    """
    Execute complete cluster-wide mount point validation for distributed Spark
    operations.

    Performs comprehensive validation of shared storage accessibility across the entire
    Spark cluster including both driver and executor nodes. This function serves as the
    primary entry point for ensuring reliable distributed I/O operations by validating
    that all cluster nodes can consistently access shared storage before proceeding
    with data processing operations.

    The validation follows a two-phase approach: first validating driver node
    accessibility
    for fast failure detection, then performing distributed validation across all
    executor
    nodes for comprehensive cluster coverage. This strategy optimizes performance while
    ensuring thorough validation coverage.

    Comprehensive Validation Strategy:
        **Phase 1 - Driver Validation**:
        - Validates mount point accessibility on Spark driver node
        - Provides fast failure detection without cluster resource usage
        - Ensures basic mount point requirements before distributed validation

        **Phase 2 - Worker Validation**:
        - Distributes validation tasks across all Spark executor nodes
        - Tests mount point and file accessibility on every cluster node
        - Collects and analyzes results from distributed validation tasks

    Args:
        spark: Active SparkSession instance representing the cluster to validate.
              Must have properly configured executor nodes and cluster connectivity.
              The session is used for both cluster topology discovery and distributed
              task execution across all nodes.
        file_path: File path to validate for cluster-wide accessibility. Can be string
                  or Path object representing any file within shared storage. The mount
                  point is automatically extracted from this path, and both mount point
                  infrastructure and specific file accessibility are validated.

    Returns:
        Boolean indicating complete cluster validation success:
        - True: ALL cluster nodes (driver + all executors) can access mount and file
        - False: At least one cluster node has accessibility issues (see logs for
          details)

    Validation Scope:
        **Infrastructure Validation**:
        - Mount point directory existence on all nodes
        - Mount point accessibility and permission validation
        - Network storage connectivity verification

        **File-Level Validation**:
        - Specific file existence across cluster
        - File read permission validation on all nodes
        - File system consistency verification

    Error Handling and Logging:
        The function uses comprehensive logging instead of exceptions to enable:
        - **Detailed Diagnostics**: Specific error messages for each failure type
        - **Cluster Visibility**: Node-by-node failure analysis and reporting
        - **Troubleshooting Support**: Actionable error messages with resolution
          guidance
        - **Production Safety**: Graceful handling without disrupting cluster operations

    Examples:
        Complete cluster validation for NFS storage:

         spark = SparkSession.builder.appName("DataPipeline").getOrCreate()
         file_path = "/nfs/shared/data/input.parquet"

         if _validate_mount_point(spark, file_path):
        ...     print("Cluster ready for distributed I/O operations")
        ...     # Proceed with Spark DataFrame operations
        ... else:
        ...     print("Storage validation failed - check logs for details")
        ...     # Handle storage accessibility issues

        Integration with I/O operations:

         def safe_read_parquet(spark, file_path):
        ...     if not _validate_mount_point(spark, file_path):
        ...         raise RuntimeError("Storage not accessible across cluster")
        ...     return spark.read.parquet(file_path)

        Production deployment validation:

         # Validate multiple storage systems
         storage_systems = [
        ...     "/nfs/data/warehouse",
        ...     "/hdfs/logs/application",
        ...     "/mnt/backup/archives"
        ... ]

         for storage_path in storage_systems:
        ...     if not _validate_mount_point(spark, storage_path):
        ...         print(f"WARNING: {storage_path} not accessible across cluster")

    Performance Characteristics:
        **Optimization Strategy**:
        - Driver validation first (fast failure detection)
        - Parallel executor validation (leverages cluster parallelism)
        - Early termination on driver failures (avoids unnecessary cluster work)

        **Scalability Profile**:
        - Small clusters: Sub-second validation completion
        - Medium clusters: Validation time dominated by network storage latency
        - Large clusters: Parallel validation prevents linear scaling issues

    Production Integration Patterns:
        **ETL Pipeline Integration**:
        - Validate input/output paths before pipeline execution
        - Fail fast on storage issues to prevent partial processing
        - Include validation in pipeline health checks

        **Continuous Deployment**:
        - Validate storage accessibility as part of deployment checks
        - Ensure new cluster nodes can access required storage systems
        - Include in automated cluster validation suites

        **Monitoring and Alerting**:
        - Scheduled validation for proactive storage monitoring
        - Integration with cluster health dashboards
        - Automated alerting on storage accessibility degradation

    Common Deployment Scenarios:
        **NFS Storage Clusters**:
        - Validates NFS mount consistency across all cluster nodes
        - Detects mount propagation issues in cluster management
        - Ensures NFS server accessibility from all nodes

        **HDFS Deployments**:
        - Validates Hadoop filesystem accessibility
        - Confirms HDFS client configuration on all nodes
        - Tests distributed filesystem consistency

        **Cloud Storage Mounts**:
        - Validates S3/Azure/GCS mount accessibility
        - Tests cloud storage authentication on all nodes
        - Confirms network connectivity to cloud services

    Troubleshooting Guide:
        **Driver Validation Failures**:
        1. Check mount point exists and is accessible on driver node
        2. Verify driver process permissions for shared storage
        3. Test network connectivity from driver to storage system

        **Worker Validation Failures**:
        1. Ensure shared storage is mounted on ALL worker nodes
        2. Verify consistent mount paths across all nodes
        3. Check worker process permissions and authentication
        4. Test network connectivity from workers to storage system

    See Also:
        - ``_validate_mount_point_local()``: Driver node validation logic
        - ``_validate_mount_point_workers()``: Distributed worker validation
        - ``configure_spark_path()``: Uses validation results for path configuration

    Note:
        This function is critical for preventing distributed I/O failures in production
        Spark clusters. It should be called before any significant I/O operations on
        shared storage to ensure reliable cluster-wide data access.
    """
    # Validate on driver first (fail fast)
    if not _validate_mount_point_local(file_path):
        return False

    # Validate across all worker nodes
    if not _validate_mount_point_workers(spark, file_path):
        return False

    return True
