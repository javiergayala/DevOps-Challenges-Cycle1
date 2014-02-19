<?php
/**
 * challenge4.php
 *
 * This file provides my answer for challenge4 of the DevOps Challenge
 * @author Javier Ayala <jayala@rackspace.com>
 * @package  challenge4
 * @version  1.0
 */
require 'vendor/autoload.php';

use OpenCloud\Rackspace;

/**
 * @var string The path to the file containing credentials
 */
$credsFile = $_SERVER['HOME'] . "/.rackspace_cloud_credentials";
/**
 * @var string Container name
 */
$container = 'my_test';
/**
 * @var string Location of the directory to upload
 */
$upload_dir = $_SERVER['HOME'] . "/upload_dir";
/**
 * OpsChallenge4
 * 
 * Class to create a Cloud-Files container, upload files to it, CDN Enable it,
 * and print out the CDN URL.
 */

class OpsChallenge4 {


    /**
     * credsFile
     * @var string
     */

    protected $credsFile;

    /**
     * setCredsFile
     * @param string $value
     * @return void
     */
    public function setCredsFile($value) {
        $this->credsFile = $value;
    }

    /**
     * getCredsFile
     * @return string
     */
    public function getCredsFile() {
        return $this->credsFile;
    }

    /**
     * conn
     * @var object
     */

    public $conn;

    /**
     * setConn
     * @param object $value
     * @return void
     */
    public function setConn($value) {
        $this->conn = $value;
    }
    /**
     * getConn
     * @return object
     */
    public function getConn() {
        return $this->conn;
    }

    /**
     * service
     * @var object
     */

    public $service;

    /**
     * setService
     * @param object $value
     * @return void
     */
    public function setService($value) {
        $this->service = $value;
    }
    /**
     * getService
     * @return object
     */
    public function getService() {
        return $this->service;
    }

    /**
     * cloud_container
     * @var object
     */
    public $cloud_container;
    /**
     * cdn_container
     * @var object
     */
    public $cdn_container;

    /**
     * setCloud_container
     * @param object $value
     * @return void
     */
    public function setCloud_container($value) {
        $this->cloud_container = $value;
    }
    /**
     * getCloud_container
     * @return object
     */
    public function getCloud_container() {
        return $this->cloud_container;
    }

    /**
     * setCdn_container
     * @param object $value
     * @return void
     */
    public function setCdn_container($value) {
        $this->cdn_container = $value;
    }
    /**
     * getCdn_container
     * @return object
     */
    public function getCdn_container() {
        return $this->cdn_container;
    }

    /**
     * upload_dir
     * @var string
     */

    public $upload_dir;

    /**
     * setUpload_dir
     * @param $value
     * @return void
     */
    public function setUpload_dir($value) {
        $this->upload_dir = $value;
    }
    /**
     * getUpload_dir
     * @return string
     */
    public function getUpload_dir() {
        return $this->upload_dir;
    }

    /**
     * __construct
     * @param string $credsFile Location of Credentials File
     * @return void
     */
    public function __construct($credsFile) {
        $this->setCredsFile($credsFile);
        $credsInfo = parse_ini_file($this->getCredsFile());
        if ($credsInfo == false) {
            throw new Exception("Missing or unreadable INI file: " . $this->getCredsFile() . "\n");
        }
        $this->setConn(new Rackspace(Rackspace::US_IDENTITY_ENDPOINT, array(
            'username'  => $credsInfo['username'],
            'apiKey'    => $credsInfo['api_key'],
            )));
        $this->setService($this->getConn()->objectStoreService('cloudFiles', 'IAD'));
    }

    /**
     * container_check
     * @return string
     */
    public function container_check() {
        return $this->getCloud_container()->getObjectCount();
    }

    /**
     * container_create
     * @param string $value Container name
     * @return void
     */
    public function container_create($value) {
        printf("Attempting to create container \"%s\": ", $value);
        $this->setCloud_container($this->getService()->createContainer($value));
        if (!$this->getCloud_Container()) {
            printf("ERROR\n");
            printf("There was an API problem! You most likely already have a container by this name.\n");
            exit();
        }
        printf("OK\n"); 
    }

    /**
     * container_upload
     * @param string $value Upload directory
     * @return void
     */
    public function container_upload($value) {
        printf("Uploading\n");
        $this->getCloud_container()->uploadDirectory($value);
        printf("Refreshing Info on Container %s\n", $this->getCloud_container()->name);
        $this->setCloud_container($this->getService()->getContainer($this->getCloud_container()->name));
    }

    /**
     * container_enable_cdn
     * @return void
     */
    public function container_enable_cdn() {
        printf("Enabling CDN\n");
        $this->getCloud_container()->enableCdn();
        // Refresh the object
        $this->setCloud_container($this->getService()->getContainer($this->getCloud_container()->name));
        // Set the CDN container info
        $this->setCdn_container($this->getCloud_container()->getCdn());
    }

}

$chall4 = new OpsChallenge4($credsFile);
$chall4->container_create($container); // Create the container
$chall4->container_upload($upload_dir);  //Upload the files
// Print out how many files were uploaded
printf("Objects now in the container: %s\n", $chall4->container_check());
$chall4->container_enable_cdn(); //Enable the CDN
// Print out the CDN URI for the container
printf("CDN URI: %s\n", $chall4->getCdn_container()->getCdnUri());
?>