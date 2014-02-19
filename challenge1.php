<?php
/**
 * challenge1.php
 *
 * This file provides my answer for challenge1 of the DevOps Challenge
 * @author Javier Ayala <jayala@rackspace.com>
 * @package  challenge1
 * @version  1.0
 */

/**
 * Load the php-opencloud classes
 */
require 'vendor/autoload.php';

use OpenCloud\Rackspace;
use OpenCloud\Compute\Constants\Network;
use OpenCloud\Compute\Constants\ServerState;

/**
 * @var string The path to the file containing credentials
 */
$credsFile = $_SERVER['HOME'] . "/.rackspace_cloud_credentials";
/**
 * @var string The ID of the flavor (as a string)
 */
$flavor = '2';
/**
 * @var string The ID of the install image
 */
$image = '2ab974de-9fe5-4f5b-9d58-766a59f3de61';
/**
 * @var string The name to use when creating a server
 */
$name = 'TestServer';

/**
 * OpsChallenge class
 * 
 * Class to build a 512MB Cloud Server and return the root password and IP Address.
 *
 * @category challenge1
 * @author Javier Ayala <jayala@rackspace.com>
 **/
class OpsChallenge
{
    /**
     * @var string The location of the credentials file
     */
    protected $credsFile;
    /**
     * @var string The name of the server
     */
    protected $name;
    /**
     * @var object Client connection object to the Rackspace Cloud API
     */
    public $conn;
    /**
     * @var object Compute service object
     */
    public $service;
    /**
     * @var resource HTTPResponse
     */
    public $response;
    #public $server;
    /**
     * @var object Server flavor object reference
     */
    public $svrflavor;
    /**
     * @var object Server image object reference
     */
    public $svrimage;
    /**
     * @var array An array containing the server admin passwords by server ID
     */
    public $serverpw = array();
    /**
     * @var string The ID of the last server created
     */
    public $lastsvr;
    
    /**
     * __construct
     *
     * Parse the credentials file and create a connection when a new instantiation is performed
     *
     * @param string $credsFile A string containing the path to the file that contains the authentication credentials.
     * @return void
     */
    public function __construct($credsFile)
    {
        $this->credsFile = $credsFile;
        $credsInfo = parse_ini_file($this->credsFile);
        if ($credsInfo == false) {
            throw new Exception("Missing or unreadable INI file: " . $this->credsFile . "\n");
        }
        $this->conn = new Rackspace(Rackspace::US_IDENTITY_ENDPOINT, array(
            'username'  => $credsInfo['username'],
            'apiKey'    => $credsInfo['api_key'],
            ));
        $this->service = $this->conn->computeService('cloudServersOpenStack', 'DFW');
    }

    /**
     * print_flavors
     *
     * Prints a list of the flavors available to standard output
     *
     * @return void
     **/
    public function print_flavors()
    {
        $flavors = $this->service->FlavorList();
        while($flavor = $flavors->Next()) {
            printf("%2d) Flavor %s has %dMB of RAM, %d vCPUs and %dGB of disk\n",
                $flavor->id, $flavor->name, $flavor->ram, $flavor->vcpus, $flavor->disk);
        }
    }

    /**
     * print_images
     *
     * Prints a list of the images available to standard output
     *
     * @return void
     **/
    function print_images()
    {
        $images = $this->service->imageList();
        $image_choice = 0;
        foreach ($images as $image) {
            printf("%d) %s: Image %s requires min. %dMB of RAM and %dGB of disk\n",
                $image_choice, $image->id, $image->name, $image->minRam,
                $image->minDisk);
            $image_choice += 1;
        }
    }

    /**
     * create_server
     *
     * Creates a cloud server
     *
     * @param string $flavor ID of the server flavor
     * @param string $image ID of the image to use for the install
     * @param string $name Name of the server to create
     * @return void
     **/
    function create_server($flavor, $image, $name)
    {
        $this->server = $this->service->server();
        $this->svrflavor = $this->service->flavor($flavor);
        $this->svrimage = $this->service->image($image);
        try {
            $this->response = $this->server->create(array(
                'name'     => $name,
                'image'    => $this->svrimage,
                'flavor'   => $this->svrflavor,
                'networks' => array(
                    $this->service->network(Network::RAX_PUBLIC),
                    $this->service->network(Network::RAX_PRIVATE)
                )
            ));
        } catch (\Guzzle\Http\Exception\BadResponseException $e) {

            // No! Something failed. Let's find out:
            $responseBody = (string) $e->getResponse()->getBody();
            $statusCode   = $e->getResponse()->getStatusCode();
            $headers      = $e->getResponse()->getHeaderLines();
            echo sprintf('Status: %s\nBody: %s\nHeaders: %s', $statusCode, $responseBody, implode(', ', $headers));
        }
        $json_result = json_decode($this->response->getBody(), true);
        $this->serverpw[$json_result['server']['id']] = $json_result['server']['adminPass'];
        $this->lastsvr = $json_result['server']['id'];
    }
    /**
     * get_connect_info
     *
     * Watch server progress, then output the ID of the server, IPv4 and IPv6 admin IP's and the admin Password to standard output.
     *
     * @return void
     **/
    function get_connect_info()
    {
        $this->server = $this->service->server($this->lastsvr);
        printf("Build completion percentage: ");
        while ($this->server->accessIPv4 == '' || $this->server->accessIPv6 == '') {
            printf(".%d.", $this->server->progress);
            sleep(10);
            $this->server = $this->service->server($this->lastsvr);
        }
        printf("\n");
        printf("Connect info for server %s:\n", $this->server->id);
        printf("IP: %s (IPv4) or %s (IPv6)\n", $this->server->accessIPv4, $this->server->accessIPv6);
        printf("Admin password: %s\n", $this->serverpw[$this->lastsvr]);
    }
} // END class 

# Create an instance to connect to the API
$chall1 = new OpsChallenge($credsFile);
# Create a server, providing the flavor ID, image ID and server name
$chall1->create_server($flavor, $image, $name);
# Retrieve and output the connection information.
$chall1->get_connect_info();

?>