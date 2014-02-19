<?php
/**
 * challenge2.php
 *
 * This file provides my answer for challenge2 of the DevOps Challenge
 * @author Javier Ayala <jayala@rackspace.com>
 * @package  challenge2
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
 * @var string The path to the file containing the SSH Key to be injected for root
 */
$sshkey = $_SERVER['HOME'] . '/.ssh/id_rsa.pub';
/**
 * @var string The ID of the flavor (as a string)
 */
$flavor = '2';
/**
 * @var string The ID of the install image
 */
$image = '2ab974de-9fe5-4f5b-9d58-766a59f3de61';
/**
 * @var string The options to allow from the commandline
 *
 *      -n: int Number of servers
 *      -f: int Flavor of server
 *      -i: string Image to use to create server
 *      -s: string Server name
 */
$opts = "n:f:i:s:";
$options = getopt($opts);
if (isset($options["n"])) {
    $numservers = intval(filter_var($options["n"], FILTER_SANITIZE_NUMBER_INT));
} else {
    $numservers = Null;
}
if (isset($options["f"])) {
    $flavor = filter_var($options["f"], FILTER_SANITIZE_STRING);
}
if (isset($options["i"])) {
    $image = filter_var($options["i"], FILTER_SANITIZE_STRING);
}
if (isset($options["s"])) {
    $svrname = filter_var($options["s"], FILTER_SANITIZE_STRING);
} else {
    $svrname = Null;
}
/**
 * OpsChallenge2 class
 * 
 * Class to build between 1-3 512MB Cloud Servers (based on user input), inject 
 * an SSH public key for logins, and return the IP address.  Server names should be
 * incremented based on user input (i.e. www-1.domain.com, www-2.domain.com, etc.)
 *
 * @category challenge2
 * @author Javier Ayala <jayala@rackspace.com>
 **/
class OpsChallenge2
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
     * @var array The IDs of the servers created
     */
    public $builtsvrs = array();
    /**
     * @var int The number of server to create
     */
    public $numservers;
    /**
     * @var string Server hostname base name
     */
    public $hnbase;
    /**
     * @var string Server hostname domain name
     */
    public $domain;
    /**
     * @var string SSH Key that is injected to created servers
     */
    public $sshkey;
    
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
     * @param string $sshkey Location of the sshkey file to use
     * @return void
     **/
    function create_server($flavor, $image, $name, $sshkey=Null)
    {
        $sshkeyloc = $sshkey;
        $this->server = $this->service->server();
        $this->svrflavor = $this->service->flavor($flavor);
        $this->svrimage = $this->service->image($image);
        if (!is_null($sshkeyloc) && file_exists($sshkeyloc)) {
            $sshkeyfh = fopen($sshkeyloc, "r");
            $this->sshkey = fread($sshkeyfh, filesize($sshkeyloc));
            fclose($sshkeyfh);
        }
        if (isset($this->sshkey)) {
            $this->server->addFile('/root/.ssh/authorized_keys', $this->sshkey);
        }
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
        array_push($this->builtsvrs, $json_result['server']['id']);
    }

    /**
     * get_connect_info
     *
     * Watch server progress, then output the ID of the server, IPv4 and IPv6 admin IP's and the admin Password to standard output.
     *
     * @param string $server ServerID of the server to get connection info for
     * @return void
     **/
    function get_connect_info($server)
    {
        $server = $server;
        $this->server = $this->service->server($server);
        if ($this->server->status != 'ACTIVE') {
            printf("Build completion percentage for %s: ", $this->server->name);
            while ($this->server->accessIPv4 == '' || $this->server->accessIPv6 == '') {
                printf(".%d.", $this->server->progress);
                sleep(10);
                $this->server = $this->service->server($server);
            }
        }
        printf("\n\n");
        printf("Connect info for server %s (%s):\n", $this->server->name, $this->server->id);
        printf("IP: %s (IPv4) or %s (IPv6)\n", $this->server->accessIPv4, $this->server->accessIPv6);
        printf("Admin password: %s\n", $this->serverpw[$server]);
    }

    /**
     * verify_num_servers
     *
     * Verify that we have a numeric value to use for building servers.
     *
     * @param int $numservers The number to verify. Defines how many servers to build.
     * @return int
     **/
    function verify_num_servers($numservers=Null)
    {
        $svrsToVerify = $numservers;
        $pattern = '/^[1-3]$/';
        while (is_null($svrsToVerify) || (($svrsToVerify < 1) || ($svrsToVerify > 3))) {
            $svrsToVerify = readline("How many servers [1-3]: ");
            $svrsToVerify = filter_var($svrsToVerify, FILTER_SANITIZE_NUMBER_INT);
            if (!preg_match($pattern, $svrsToVerify, $matches)){
                $svrsToVerify = Null;
                printf("Must input a number from 1 to 3\n");
            }
        }
        return $svrsToVerify;
    }

    /**
     * verify_server_base
     *
     * Verify that we have a name to use for building servers.
     *
     * @param string $svrname The servername to use as a base for the new server names.
     * @return void
     **/
    function verify_server_base($svrname=Null)
    {
        $nameToVerify = $svrname;
        $hnregex = '/([a-zA-Z0-9](-*[a-zA-Z0-9]+)*)((\.)[a-zA-Z0-9](-*[a-zA-Z0-9]+)*(\.[a-zA-Z0-9](-*[a-zA-Z0-9]+)*)+)/';
        while (!preg_match($hnregex, $nameToVerify, $matches)) {
            $nameToVerify = readline("Servername to use (e.g. test.domain.com): ");
            $nameToVerify = filter_var($nameToVerify, FILTER_SANITIZE_STRING);
        }
        $this->hnbase = $matches[1] . "-";
        $this->domain = $matches[3];
        return;
    }
} // END class 

# Create an instance to connect to the API
$chall2 = new OpsChallenge2($credsFile);

# Determine how many servers to create and verify it's validity
$numservers = $chall2->verify_num_servers($numservers);

# Determine the validity of the server name to use as a template for the new names
$svrname = $chall2->verify_server_base($svrname);

# Provide output regarding the options to be used
printf("Number of servers: %d\n", $numservers);
printf("Flavor: %s\n", $flavor);
printf("Image: %s\n", $image);

# Create the server(s), providing the flavor ID, image ID, server name and SSHKey file location
for ($i=1; $i <= $numservers; $i++) { 
    $server = $chall2->hnbase . $i . $chall2->domain;
    $chall2->create_server($flavor, $image, $server, $sshkey);
}

# Watch for the builds to complete, then output the connection information.
while ($server = array_pop($chall2->builtsvrs)) {
    $chall2->get_connect_info($server);
}

?>