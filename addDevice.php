<?php

include_once('vamsi.php');

$ip = $_GET['ip'];
$port = $_GET['port'];
$community = $_GET['community'];
$version = $_GET['version'];

if(empty($ip) || empty($port)||empty($community) || empty($version)) {
    echo "FALSE";
}

else {
    $output = $database->query('SELECT * FROM switches');
    $count = 0;
    foreach ($output as $output) {
        if($output['ip']==$ip && $output['port']==$port && $output['community']==$community && $output['version']==$version){
            $count = $count+1;
        }
    }

    if ($count ==0){
        $database->exec("INSERT INTO switches (ip,port,community,version) VALUES ('$ip','$port','$community','$version')");
        echo "OK";
    }
    else {
        echo "FALSE";
    }
}

$database->close();

?>
