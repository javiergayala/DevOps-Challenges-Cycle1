<?php
/**
 * challenge3.php
 *
 * This file provides my answer for challenge3 of the DevOps Challenge
 * @author Javier Ayala <jayala@rackspace.com>
 * @package  challenge3
 * @version  1.0
 */

/**
 * Load the php-opencloud classes
 */
require 'vendor/autoload.php';

use OpenCloud\Rackspace;

/**
 * @var string The path to the file containing credentials
 */
$credsFile = $_SERVER['HOME'] . "/.rackspace_cloud_credentials";

/**
 * OpsChallenge3 class
 *
 * @category challenge3
 * @author Javier Ayala <jayala@rackspace.com>
 **/
class OpsChallenge3
{
    /**
     * @var string The location of the credentials file
     */
    protected $credsFile;
    /**
     * @var object Client connection object to the Rackspace Cloud API
     */
    public $conn;
    /**
     * @var object DNS service object
     */
    public $service;
    /**
     * @var array Domains contained within the DNS
     */
    public $domains;
    /**
     * @var int Domain selected from the list
     */
    public $domain_id = Null;
    /**
     * @var int Domain names and ID's stored in the database
     */
    public $domainnames;
    
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
        $this->service = $this->conn->dnsService(Null, 'DFW');
        $this->domains = $this->service->domainList();
    }
    /**
     * list_domains function
     *
     * @return void
     **/
    function select_domain()
    {
        /**
         * @var array List of domain names
         */
        $this->domainnames = array();
        $this->domain_id = Null;
        foreach ($this->domains as $d) {
            array_push($this->domainnames, array('name' => $d->name, 'id' => $d->id));
        }
        printf("Found the following domains:\n");
        for ($i=0; $i < count($this->domainnames); $i++) { 
            printf("%2d: %s\n", $i, $this->domainnames[$i]['name']);
        }
        while (is_null($this->domain_id) || (($this->domain_id < 0) || ($this->domain_id > count($this->domainnames)))) {
            $this->domain_id = readline("Choose the domain to modify: ");
            $this->domain_id = filter_var($this->domain_id, FILTER_SANITIZE_NUMBER_INT);
        }
        printf("You chose %2d: %s (ID: %s)\n", $this->domain_id,
            $this->domainnames[$this->domain_id]['name'],
            $this->domainnames[$this->domain_id]['id']);
    }
    /**
     * add_a_record
     *
     * Add an A record to the DNS
     *
     * @return void
     **/
    function add_a_record()
    {
        /**
         * @var str IP Address for the A record
         * @var int TTL for the A record
         * @var str Hostname for the A record
         * @var str Regex to Validate IPv4 Addresses
         */
        $ip = Null;
        $ttl = Null;
        $host = Null;
        $hnregex = "/(([a-zA-Z0-9](-*[a-zA-Z0-9]+)*).)+" . $this->domainnames[$this->domain_id]['name'] . "/";
        $shnregex = "/^(([a-zA-Z0-9](-*[a-zA-Z0-9]+)*).)/";
        while (!is_string($ip)) {
            $ip = filter_var(readline("IP Address: "), FILTER_VALIDATE_IP, FILTER_FLAG_IPV4);
        }
        while (!is_int($ttl)) {
            $ttl = filter_var(readline("TTL [300]: "), FILTER_VALIDATE_INT);
            $ttl = (!is_bool($ttl)) ? $ttl : 300;
        }
        while (!is_string($host)) {
            $hosttmp = readline("Hostname for new A record: ");
            if (filter_var($hosttmp, FILTER_VALIDATE_REGEXP, array('options' => array('regexp' => $hnregex)))) {
                $host = $hosttmp;
            } elseif (filter_var($hosttmp, FILTER_VALIDATE_REGEXP, array('options' => array('regexp' => $shnregex)))) {
                $host = filter_var($hosttmp . "." . $this->domainnames[$this->domain_id]['name'], FILTER_VALIDATE_REGEXP, array('options' => array('regexp' => $hnregex)));
            }
        }

        foreach ($this->domains as $d) {
            if ($d->name == $this->domainnames[$this->domain_id]['name']){
                $domain = $d;
            }
        }

        $record = array(
            'name' => $host,
            'type' => 'A',
            'ttl' => $ttl,
            'data' => $ip);

        printf("\nYou would like to add the following record:\n");
        printf("Type: %s\n", $record['type']);
        printf("Name: %s\n", $record['name']);
        printf("IP: %s\n", $record['data']);
        printf("TTL: %s\n", $record['ttl']);

        $proceed = readline("Type \"Y\" or \"y\" to proceed: ");

        if (strtolower($proceed) === 'y') {
            $hostentry = $domain->record($record);
            try {
                $response = $hostentry->create();
                printf("Created!\n");
            } catch (Exception $e) {
                printf("%s\n", $e);
            }
        } else {
            printf("ABORTED!\n");
        }
    }
} // END class 

# Create an instance to connect to the API
$chall3 = new OpsChallenge3($credsFile);

$chall3->select_domain();
printf("%s\n", $chall3->domainnames[$chall3->domain_id]['name']);
$chall3->add_a_record();
?>